"""断言计算引擎 - 核心工具类"""
import re
from typing import Any

class AssertionEngine:
    """增强型比较引擎：支持中英文及符号映射"""

    # 操作符映射表（中文、英文、符号）
    OP_MAP = {
        'eq': 'eq', '==': 'eq', '=': 'eq', '等于': 'eq',
        'ne': 'ne', '!=': 'ne', '<>': 'ne', '不等于': 'ne',
        'gt': 'gt', '>': 'gt', '大于': 'gt',
        'lt': 'lt', '<': 'lt', '小于': 'lt',
        'ge': 'ge', '>=': 'ge', '大于等于': 'ge',
        'le': 'le', '<=': 'le', '小于等于': 'le',
        'contains': 'contains', '包含': 'contains','in': 'contains',
        'not_contains': 'not_contains', '不包含': 'not_contains', 'not_in': 'not_contains',
        'startswith': 'startswith', '开头是': 'startswith',
        'endswith': 'endswith', '结尾是': 'endswith',
        'regex': 'regex', '正则': 'regex',
        'null': 'null', 'is_null': 'null', '为空': 'null',
        'not_null': 'not_null', 'is_not_null': 'not_null', '不为空': 'not_null',
        # 新增：数值类型校验
        'is_numeric': 'is_numeric', 'numeric': 'is_numeric', 'number': 'is_numeric',
        '是数字': 'is_numeric', '数值类型': 'is_numeric', '数字类型': 'is_numeric'
    }

    @classmethod
    def compare(cls, actual: Any, expected: Any, operator: str = 'eq') -> bool:
        """核心比较逻辑"""
        op = cls.OP_MAP.get(str(operator).lower(), 'eq')

        # 1. 空值断言 (忽略 expected)
        if op == 'null': return actual is None or str(actual).lower() == 'null'
        if op == 'not_null': return actual is not None and str(actual).lower() != 'null'

        # 2. 类型/格式校验 (忽略 expected)
        if op == 'is_numeric':
            if actual is None: return False
            try:
                float(str(actual))
                return True
            except (ValueError, TypeError):
                return False

        # 3. 基础断言
        if op == 'eq': return str(actual) == str(expected)
        if op == 'ne': return str(actual) != str(expected)

        # 4. 数值比较断言
        try:
            if op == 'gt': return float(actual) > float(expected)
            if op == 'lt': return float(actual) < float(expected)
            if op == 'ge': return float(actual) >= float(expected)
            if op == 'le': return float(actual) <= float(expected)
        except (ValueError, TypeError):
            pass

        # 5. 文本断言
        act_s, exp_s = str(actual), str(expected)
        if op == 'contains': return exp_s in act_s
        if op == 'not_contains': return exp_s not in act_s
        if op == 'startswith': return act_s.startswith(exp_s)
        if op == 'endswith': return act_s.endswith(exp_s)
        if op == 'regex': return bool(re.search(exp_s, act_s))

        return False

    @classmethod
    def get_desc(cls, operator: str) -> str:
        """获取操作符的友好描述"""
        desc_map = {
            'eq': '等于', 'ne': '不等于', 'gt': '大于', 'lt': '小于',
            'ge': '大于等于', 'le': '小于等于', 'contains': '包含',
            'not_contains': '不包含', 'startswith': '以...开头',
            'endswith': '以...结尾', 'regex': '正则匹配',
            'null': '为空', 'not_null': '不为空',
            'is_numeric': '是数字'
        }
        internal_op = cls.OP_MAP.get(str(operator).lower(), 'eq')
        return desc_map.get(internal_op, operator)