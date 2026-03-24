"""Skill 动作 - 通过自然语言触发 Skill"""
from typing import Any, Dict

from actions.action_registry import action_registry
from actions.base import ExecutionAction, ActionMetadata
from actions.skill_discoverer import SkillDiscoverer


@action_registry.register_decorator()
class SkillAction(ExecutionAction):
    """Skill 动作 - 通过自然语言触发 Skill"""

    metadata = ActionMetadata(
        name='skill',
        category='skill',
        description='通过自然语言触发 Skill 执行任务，框架会自动解析参数并调用对应的 Skill 脚本',
        parameters=[
            {
                'name': '描述',
                'type': 'str',
                'required': True,
                'description': '自然语言描述，如 "生成批量入仓测试Excel文件"'
            },
            {
                'name': 'skill_name',
                'type': 'str',
                'required': False,
                'description': 'Skill 名称（可选，如果描述中已包含则无需填写）'
            },
            {
                'name': 'action',
                'type': 'str',
                'required': False,
                'description': 'Skill 动作名称（可选）'
            },
            {
                'name': 'params',
                'type': 'dict',
                'required': False,
                'description': '直接参数（可选，如果只有描述则自动解析）'
            }
        ],
        returns={
            'status': 'SUCCESS/FAILED',
            'output': 'Skill 执行结果',
            'parsed_params': 'LLM 解析后的参数'
        },
        examples=[
            {
                'description': '自然语言触发 skill',
                'yaml': '''
- intent: "前置1：生成批量入仓测试数据"
  action: "skill"
  params:
    描述: "为批量入仓接口生成测试数据，包括tidb的user表和mysql的order表，success场景"
'''
            }
        ]
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        """执行 Skill 动作"""
        description = params.get('描述') or params.get('description')
        skill_name = params.get('skill_name')
        action = params.get('action')
        direct_params = params.get('params', {})
        save_to_context = params.get('save_to_context', 'skill')
        
        # 1. 直接参数模式
        if skill_name and direct_params:
            result = self._execute_bridge_skill(skill_name, action, direct_params)
            # 将 Skill 执行结果保存到测试上下文，供后续步骤使用
            if context and save_to_context:
                context.set(save_to_context, result)
            return result
        
        # 2. 自然语言解析模式
        if description:
            return self._execute_by_description(description, skill_name, action, direct_params, save_to_context, context)
        
        return {
            'status': 'FAILED',
            'message': '缺少必填参数: 描述 或 skill_name'
        }

    def _execute_by_description(self, description: str, skill_name: str, action: str, direct_params: Dict, save_to_context: str, context) -> Dict[str, Any]:
        """通过自然语言描述执行"""
        print(f"\n[Skill] 正在解析自然语言: {description}")
        
        parsed = SkillDiscoverer.llm_parse(description)
        
        if 'error' in parsed:
            return {
                'status': 'FAILED',
                'message': f'LLM 解析失败: {parsed["error"]}'
            }
        
        print(f"[Skill] LLM 解析结果: {parsed}")
        
        # 检测场景类型并更新
        parsed = self._apply_scenario_detection(description, parsed)
        
        # 解析结果可能是单条或批量
        if isinstance(parsed, list):
            return self._execute_batch(parsed, save_to_context, context)
        else:
            return self._execute_single(parsed, direct_params, save_to_context, context)

    def _apply_scenario_detection(self, description: str, parsed: Dict) -> Dict:
        """应用场景检测"""
        detected = SkillDiscoverer.detect_scenario(description)
        print(f"[Skill] 检测到场景类型: {detected}")
        
        if detected and isinstance(parsed, dict):
            params = parsed.get('params', {})
            params['scenario'] = detected
            parsed['params'] = params
            print(f"[Skill] 更新 params: {params}")
        
        return parsed

    def _execute_single(self, parsed: Dict, direct_params: Dict, save_to_context: str, context) -> Dict[str, Any]:
        """执行单条解析结果"""
        skill_name = parsed.get('skill_name')
        action = parsed.get('action')
        
        # 强制使用 batch_workflow（更稳定）
        if skill_name == 'jdbc-warehouse-test':
            action = 'batch_workflow'
        
        params = {**direct_params, **parsed.get('params', {})}
        
        result = self._execute_bridge_skill(skill_name, action, params)
        
        if save_to_context and context:
            context.set(save_to_context, result)
        
        return result

    def _execute_batch(self, parsed_list: list, save_to_context: str, context) -> Dict[str, Any]:
        """批量执行解析结果"""
        results = []
        for item in parsed_list:
            result = self._execute_bridge_skill(
                item.get('skill_name'),
                item.get('action'),
                item.get('params', {})
            )
            results.append(result)
        
        batch_result = {
            'status': 'SUCCESS',
            'message': f'批量执行 {len(results)} 个 skill',
            'results': results
        }
        
        if save_to_context and context:
            context.set(save_to_context, batch_result)
        
        return batch_result

    def _execute_bridge_skill(self, skill_name: str, action: str, params: Dict) -> Dict[str, Any]:
        """委托给 BridgeSkillAction 执行"""
        from actions.generic.bridge_skill import BridgeSkillAction
        
        bridge = BridgeSkillAction()
        return bridge.execute(
            {},
            skill_name=skill_name,
            action=action,
            **params
        )
