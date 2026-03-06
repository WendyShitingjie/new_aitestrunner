"""通用断言动作（非数据库场景）"""
from typing import Any, Dict
from actions.action_registry import action_registry
from actions.base import ExecutionAction, ActionMetadata
from utils.assertion_engine import AssertionEngine


@action_registry.register_decorator()
class AssertValueAction(ExecutionAction):
    """通用值断言动作"""

    metadata = ActionMetadata(
        name='assert_value',
        category='assertion',
        description='断言任意给定的两个值是否满足条件（支持中英文操作符）',
        parameters=[
            {
                'name': 'actual',
                'type': 'any',
                'required': True,
                'description': '实际值（通常来自上一步的输出或变量）'
            },
            {
                'name': 'expected',
                'type': 'any',
                'required': False,
                'description': '期望值（为空判断时可不传）'
            },
            {
                'name': 'operator',
                'type': 'str',
                'required': False,
                'default': '等于',
                'description': '操作符，如：>=, 不等于, contains, 为空'
            },
            {
                'name': 'message',
                'type': 'str',
                'required': False,
                'description': '自定义断言描述，用于识别此断言的目的'
            }
        ],
        returns={
            'status': 'PASS/FAIL',
            'reason': '结果描述'
        }
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        self.validate_parameters(params)

        actual = params['actual']
        expected = params.get('expected')
        operator = params.get('operator', 'eq')
        message = params.get('message', '值校验')

        is_pass = AssertionEngine.compare(actual, expected, operator)
        op_desc = AssertionEngine.get_desc(operator)

        reason = f"[{message}] 判定{op_desc}成功" if is_pass else \
            f"[{message}] 判定失败：期望 {op_desc} '{expected}'，但实际值为 '{actual}'"

        return {
            'status': 'PASS' if is_pass else 'FAIL',
            'reason': reason,
            'details': {
                'actual': actual,
                'expected': expected,
                'operator': operator
            }
        }