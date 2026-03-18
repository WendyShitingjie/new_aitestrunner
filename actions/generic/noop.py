"""空操作动作 - 用于占位或跳过某些步骤"""
from typing import Any, Dict
from actions.action_registry import action_registry
from actions.base import ExecutionAction, ActionMetadata


@action_registry.register_decorator()
class NoOpAction(ExecutionAction):
    """空操作动作 - 不执行任何操作,直接返回成功"""

    metadata = ActionMetadata(
        name='noop',
        category='utility',
        description='空操作,不执行任何实际操作,直接返回成功状态。用于测试用例中需要占位但无需实际执行的场景。',
        parameters=[
            {
                'name': 'reason',
                'type': 'str',
                'required': False,
                'description': '跳过执行的原因说明(可选)'
            }
        ],
        returns={
            'status': 'SUCCESS',
            'message': '空操作执行成功'
        },
        examples=[
            {
                'description': '复用其他测试用例的配置,无需重复执行',
                'yaml': '''
- intent: "前置1:复用TC_001的ai_execute_config,无需重复插入"
  action: "noop"
  params:
    reason: "复用TC_001的配置"
'''
            },
            {
                'description': '占位步骤',
                'yaml': '''
- intent: "暂不执行此步骤"
  action: "noop"
  params: {}
'''
            }
        ]
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        """
        执行空操作

        Args:
            context: 执行上下文
            **params: 可选参数
                - reason: 跳过原因说明

        Returns:
            Dict: 固定返回成功状态
        """
        reason = params.get('reason', '无')

        return {
            'status': 'SUCCESS',
            'message': f'空操作执行成功 (原因: {reason})',
            'reason': reason
        }
