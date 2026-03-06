"""执行引擎"""
from typing import Any, Dict, List
from datetime import datetime
import yaml
import time

from .context import ExecutionContext
from .intent_parser import IntentParser, ParsedIntent
from actions.action_registry import ActionRegistry
from .html_reporter import HTMLReporter
from .param_resolver import ParamResolver


class TestResult:
    """测试结果"""
    
    def __init__(self, test_case_id: str, test_name: str, status: str,
                 execution_time: float, assertions: List[Dict],
                 context_snapshot: Dict, business_analysis: Dict):
        self.test_case_id = test_case_id
        self.test_name = test_name
        self.status = status
        self.execution_time = execution_time
        self.assertions = assertions
        self.context_snapshot = context_snapshot
        self.business_analysis = business_analysis


class AITestExecutor:
    """AI测试执行器"""

    def __init__(self, llm_client=None, knowledge_base=None, enable_html_report=True):
        """
        初始化执行器

        Args:
            llm_client: LLM客户端
            knowledge_base: 知识库
            enable_html_report: 是否启用HTML报告
        """
        self.intent_parser = IntentParser(llm_client, knowledge_base) if llm_client else None
        self.action_registry = ActionRegistry()
        self.context = ExecutionContext()
        self.enable_html_report = enable_html_report
        self.html_reporter = HTMLReporter() if enable_html_report else None

        # 执行详情记录
        self.execution_details = {
            'preconditions': [],
            'test_steps': [],
            'assertions': [],
            'start_time': None,
            'end_time': None
        }
    
    def execute_test_case(self, test_case_yaml: str) -> TestResult:
        """
        执行测试用例

        Args:
            test_case_yaml: 测试用例YAML内容

        Returns:
            TestResult: 测试结果
        """
        # 重置执行详情（避免批量执行时累积）
        self.execution_details = {
            'preconditions': [],
            'test_steps': [],
            'assertions': [],
            'start_time': None,
            'end_time': None
        }

        # 1. 解析YAML
        test_case = yaml.safe_load(test_case_yaml)

        print(f"📋 开始执行测试用例: {test_case['test_name']}")
        print(f"🎯 业务流程: {test_case.get('business_flow', 'N/A')}")
        print(f"📜 业务规则: {test_case.get('business_rules', [])}")

        start_time = datetime.now()
        self.execution_details['start_time'] = start_time

        # 2. 初始化上下文
        context = ExecutionContext()
        if 'business_flow' in test_case:
            context.load_b_tree(test_case['business_flow'])
            context.load_a_tree(f"IMPL_{test_case['business_flow']}")

        # 3. 执行前置条件
        print("\n🔧 执行前置条件...")
        self._execute_preconditions(test_case, context)

        # ✅ 检查前置条件是否失败
        preconditions_failed = any(
            p.get('status') == 'FAIL'
            for p in self.execution_details.get('preconditions', [])
        )

        # 4. 执行测试步骤（仅当前置条件全部成功时）
        if not preconditions_failed:
            print("\n🚀 执行测试步骤...")
            self._execute_test_steps(test_case, context)
        else:
            print("\n⛔ 前置条件失败，跳过测试步骤执行")

        # 5. 执行断言（仅当前置条件和测试步骤都成功时）
        steps_failed = any(
            s.get('status') == 'FAIL'
            for s in self.execution_details.get('test_steps', [])
        )

        if not preconditions_failed and not steps_failed:
            print("\n✔️  执行断言...")
            assertion_results = self._execute_assertions(test_case, context)
        else:
            print("\n⛔ 前置条件或测试步骤失败，跳过顶层断言执行")
            assertion_results = []

        # 6. 生成测试报告
        end_time = datetime.now()
        self.execution_details['end_time'] = end_time
        execution_time = (end_time - start_time).total_seconds()

        test_result = self._generate_test_result(
            test_case,
            context,
            assertion_results,
            execution_time
        )

        print("\n" + "="*60)
        print(f"📊 测试结果: {test_result.status}")
        print(f"⏱️  执行时间: {test_result.execution_time}秒")
        print("="*60)

        # 7. 生成HTML报告
        if self.enable_html_report and self.html_reporter:
            try:
                report_path = self.html_reporter.generate_report(
                    test_case,
                    self.execution_details,
                    test_result
                )
                print(f"\n📄 HTML报告已生成: {report_path}")
            except Exception as e:
                print(f"\n⚠️  HTML报告生成失败: {str(e)}")

        return test_result
    
    def _execute_preconditions(self, test_case: Dict, context: ExecutionContext):
        """执行前置条件"""
        preconditions = test_case.get('test_intent', {}).get('preconditions', [])

        for i, precondition in enumerate(preconditions):
            print(f"\n  [{i+1}] {precondition['intent']}")

            item_start_time = datetime.now()
            item_detail = {
                'intent': precondition['intent'],
                'action': '',
                'params': {},
                'result': {},
                'status': 'SUCCESS',
                'error': '',
                'start_time': item_start_time,
                'end_time': None,
                'duration': 0
            }

            precondition_failed = False  # 标记前置条件是否失败

            try:
                # 解析意图（如果需要）
                if self.intent_parser and 'action' not in precondition:
                    parsed = self.intent_parser.parse(precondition)
                else:
                    parsed = ParsedIntent(
                        action=precondition['action'],
                        parameters=precondition.get('params', {})
                    )

                item_detail['action'] = parsed.action
                item_detail['params'] = parsed.parameters

                print(f"      → 使用动作1: {parsed.action}")

                # 解析参数（支持变量引用和函数调用）
                resolver = ParamResolver(context)
                resolved_params = resolver.resolve(parsed.parameters)

                # 将前置参数及参数值写入上下文
                self._inject_context_recursively(context, resolved_params)
                # print(f"      → 上下文: {context.get('serial_id')}")

                # 执行动作
                action = self.action_registry.get(parsed.action)
                result = action.execute(context, **resolved_params)

                item_detail['result'] = result

                # 检查动作返回的状态
                if result.get('status') in ['SUCCESS', 'PASS']:
                    item_detail['status'] = 'SUCCESS'
                    print(f"      ✅ 执行成功")
                    print(f"      → 返回: {self._format_result(result)}")
                else:
                    item_detail['status'] = 'FAIL'
                    item_detail['error'] = result.get('message', '执行失败')
                    print(f"      ❌ 执行失败: {result.get('message', '')}")
                    precondition_failed = True

            except Exception as e:
                item_detail['status'] = 'FAIL'
                item_detail['error'] = str(e)
                print(f"      ❌ 执行失败: {str(e)}")
                precondition_failed = True

            finally:
                item_end_time = datetime.now()
                item_detail['end_time'] = item_end_time
                item_detail['duration'] = (item_end_time - item_start_time).total_seconds()
                self.execution_details['preconditions'].append(item_detail)

            # ✅ 快速失败：如果前置条件失败，立即停止执行后续前置条件
            if precondition_failed:
                print(f"\n  ⛔ 前置条件失败，停止执行后续前置条件和测试步骤")
                break

    def _inject_context_recursively(self, context, data: Any):
        """
        递归地将解析后的参数存入上下文
        """
        if not isinstance(data, dict):
            return

        for key, value in data.items():
            # 1. 存入当前键值对 (例如: user_info: {uid: "..."})
            context.set(key, value)

            # 2. 如果值是字典，继续向内递归 (例如: 把内部的 uid 也存为顶层变量)
            if isinstance(value, dict):
                self._inject_context_recursively(context, value)

            # 3. 如果是列表，遍历列表（可选，看你的业务需求）
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._inject_context_recursively(context, item)

    def _execute_test_steps(self, test_case: Dict, context: ExecutionContext):
        """执行测试步骤"""
        test_steps = test_case.get('test_intent', {}).get('test_steps', [])

        for i, step in enumerate(test_steps):
            print(f"\n  [{i+1}] {step['intent']}")

            item_start_time = datetime.now()
            item_detail = {
                'intent': step['intent'],
                'action': '',
                'params': {},
                'result': {},
                'status': 'SUCCESS',
                'error': '',
                'start_time': item_start_time,
                'end_time': None,
                'duration': 0,
                'assertions': []  # 添加断言列表
            }

            step_failed = False  # 标记步骤是否失败

            try:
                # 解析意图
                if self.intent_parser and 'action' not in step:
                    parsed = self.intent_parser.parse(step)
                else:
                    parsed = ParsedIntent(
                        action=step['action'],
                        parameters=step.get('params', {})
                    )

                item_detail['action'] = parsed.action
                item_detail['params'] = parsed.parameters

                print(f"      → 使用动作2: {parsed.action}")

                # 解析参数（支持变量引用和函数调用）
                resolver = ParamResolver(context)
                resolved_params = resolver.resolve(parsed.parameters)

                # 将步骤参数及参数值写入上下文
                self._inject_context_recursively(context, resolved_params)
                # print(f"      → 上下文: {context.get('serial_id')}")

                # 执行动作
                action = self.action_registry.get(parsed.action)
                result = action.execute(context, **resolved_params)

                item_detail['result'] = result

                # 检查动作返回的状态
                if result.get('status') in ['SUCCESS', 'PASS']:
                    item_detail['status'] = 'SUCCESS'
                    print(f"      ✅ 执行成功")

                    # 执行步骤级别的断言
                    step_assertions = step.get('assertions', [])
                    if step_assertions:
                        print(f"\n      🔍 执行步骤断言 ({len(step_assertions)}个)...")
                        for j, assertion in enumerate(step_assertions):
                            assertion_result = self._execute_single_assertion(
                                assertion, context, j+1
                            )
                            item_detail['assertions'].append(assertion_result)
                            self.execution_details['assertions'].append(assertion_result)

                            # ✅ 快速失败：如果断言失败，立即停止
                            if assertion_result.get('status') == 'FAIL':
                                step_failed = True
                                print(f"\n      ⛔ 断言失败，停止执行后续断言和步骤")
                                break
                else:
                    item_detail['status'] = 'FAIL'
                    item_detail['error'] = result.get('message', '执行失败')
                    print(f"      ❌ 执行失败: {result.get('message', '')}")
                    step_failed = True

            except Exception as e:
                item_detail['status'] = 'FAIL'
                item_detail['error'] = str(e)
                print(f"      ❌ 执行失败: {str(e)}")
                step_failed = True

            finally:
                item_end_time = datetime.now()
                item_detail['end_time'] = item_end_time
                item_detail['duration'] = (item_end_time - item_start_time).total_seconds()
                self.execution_details['test_steps'].append(item_detail)

            # ✅ 快速失败：如果步骤失败，立即停止执行后续步骤
            if step_failed:
                print(f"\n  ⛔ 步骤失败，停止执行后续步骤")
                break
    
    def _execute_single_assertion(self, assertion: Dict, context: ExecutionContext,
                                   index: int) -> Dict:
        """
        执行单个断言

        Args:
            assertion: 断言配置
            context: 执行上下文
            index: 断言序号

        Returns:
            Dict: 断言执行详情
        """
        print(f"         [{index}] {assertion['intent']}")

        item_start_time = datetime.now()
        item_detail = {
            'intent': assertion['intent'],
            'action': '',
            'params': {},
            'result': {},
            'status': 'PASS',
            'error': '',
            'start_time': item_start_time,
            'end_time': None,
            'duration': 0
        }

        try:
            # 解析意图
            if self.intent_parser and 'action' not in assertion:
                parsed = self.intent_parser.parse(assertion)
            else:
                parsed = ParsedIntent(
                    action=assertion['action'],
                    parameters=assertion.get('params', {})
                )

            item_detail['action'] = parsed.action
            item_detail['params'] = parsed.parameters

            print(f"             → 使用动作3: {parsed.action}")

            # 解析参数（支持变量引用和函数调用）
            resolver = ParamResolver(context)
            resolved_params = resolver.resolve(parsed.parameters)

            # 将断言参数及参数值写入上下文
            self._inject_context_recursively(context, resolved_params)
            # print(f"      → 上下文: {context.get('serial_id')}")

            # 执行动作
            action = self.action_registry.get(parsed.action)
            result = action.execute(context, **resolved_params)

            item_detail['result'] = result

            # 判断断言状态
            if result.get('status') == 'PASS':
                item_detail['status'] = 'PASS'
                print(f"             ✅ 断言通过")
            else:
                item_detail['status'] = 'FAIL'
                item_detail['error'] = result.get('reason', '断言失败')
                print(f"             ❌ 断言失败: {result.get('reason')}")
                if result.get('details'):
                    print(f"             详情: {result.get('details')}")

        except Exception as e:
            item_detail['status'] = 'FAIL'
            item_detail['error'] = str(e)
            print(f"             ❌ 断言异常: {str(e)}")

        finally:
            item_end_time = datetime.now()
            item_detail['end_time'] = item_end_time
            item_detail['duration'] = (item_end_time - item_start_time).total_seconds()

        return item_detail

    def _execute_assertions(self, test_case: Dict, context: ExecutionContext) -> List[Dict]:
        """执行顶层断言（如果有的话）"""
        assertions = test_case.get('test_intent', {}).get('assertions', [])
        assertion_results = []

        if not assertions:
            # 如果没有顶层断言，返回空列表
            # 注意：步骤级别的断言已经在 _execute_test_steps 中执行了
            return assertion_results

        for i, assertion in enumerate(assertions):
            assertion_result = self._execute_single_assertion(assertion, context, i+1)
            assertion_results.append(assertion_result['result'])
            self.execution_details['assertions'].append(assertion_result)

        return assertion_results
    
    def _format_result(self, result: Any) -> str:
        """格式化结果输出"""
        if isinstance(result, dict):
            if 'user' in result:
                return f"user_id={result['user'].get('user_id', 'N/A')}"
            elif 'batch_no' in result:
                return f"batch_no={result['batch_no']}"
        return str(result)[:50]
    
    def _generate_test_result(self, test_case: Dict, context: ExecutionContext,
                             assertion_results: List[Dict], execution_time: float) -> TestResult:
        """生成测试报告"""
        # 从 execution_details 中获取所有断言结果（包括步骤级别的断言）
        all_assertions = self.execution_details.get('assertions', [])

        # 判断是否所有断言都通过
        all_passed = all(a.get('status') == 'PASS' for a in all_assertions) if all_assertions else True

        return TestResult(
            test_case_id=test_case.get('test_case_id', 'N/A'),
            test_name=test_case['test_name'],
            status='PASS' if all_passed else 'FAIL',
            execution_time=execution_time,
            assertions=[a.get('result', {}) for a in all_assertions],
            context_snapshot=context.snapshot(),
            business_analysis={}
        )

