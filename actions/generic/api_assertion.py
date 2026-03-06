"""API 响应断言动作 - 规范化版"""
from typing import Any, Dict
from actions.action_registry import action_registry
from actions.base import ExecutionAction, ActionMetadata
from utils.assertion_engine import AssertionEngine


@action_registry.register_decorator()
class AssertApiResponseAction(ExecutionAction):
    """API 响应断言动作"""

    metadata = ActionMetadata(
        name='assert_api_response',
        category='assertion',
        description='断言 API 响应结果（支持通过路径从响应对象中提取实际值进行比较）',
        parameters=[
            {
                'name': 'path',
                'type': 'str',
                'required': True,
                'description': '实际值提取路径。示例：status_code(状态码), body.data.id(响应体字段), headers.Content-Type'
            },
            {
                'name': 'expected',
                'type': 'any',
                'required': False,
                'description': '期望值'
            },
            {
                'name': 'operator',
                'type': 'str',
                'required': False,
                'default': '等于',
                'description': '操作符：支持 ==, >=, 包含, 不为空, 正则等'
            },
            {
                'name': 'response_var',
                'type': 'str',
                'required': False,
                'default': 'http_response',
                'description': '上下文中的响应对象变量名'
            },
            {
                'name': 'message',
                'type': 'str',
                'required': False,
                'description': '断言业务描述'
            }
        ],
        returns={
            'status': 'PASS/FAIL',
            'reason': '断言结果描述',
            'details': '包含提取出的实际值和相关配置'
        }
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        self.validate_parameters(params)

        path = params['path']
        expected = params.get('expected')
        operator = params.get('operator', 'eq')
        response_var = params.get('response_var', 'http_response')
        message = params.get('message', 'API响应断言')

        # 1. 从上下文获取响应对象
        response_obj = context.get(response_var)
        if not response_obj:
            return {
                'status': 'FAIL',
                'reason': f"未找到响应变量 '{response_var}'，请确保 call_http_api 已成功执行并保存结果"
            }

        # 2. 根据 path (路径) 提取真正用于比较的值
        actual = self._extract_by_path(response_obj, path)

        # 3. 调用统一断言引擎
        is_pass = AssertionEngine.compare(actual, expected, operator)
        op_desc = AssertionEngine.get_desc(operator)

        reason = f"[{message}] 校验成功：'{path}' {op_desc} '{expected}'" if is_pass else \
            f"[{message}] 校验失败：'{path}' 实际值为 '{actual}'，不{op_desc} '{expected}'"

        return {
            'status': 'PASS' if is_pass else 'FAIL',
            'reason': reason,
            'details': {
                'path': path,
                'actual': actual,
                'expected': expected,
                'operator': operator
            }
        }

    def _extract_by_path(self, data: Dict, path: str) -> Any:
        """从嵌套字典/列表中提取值"""
        if not data or not path:
            return None

        parts = path.split('.')
        current = data

        try:
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list) and part.isdigit():
                    current = current[int(part)]
                else:
                    return None
            return current
        except Exception:
            return None