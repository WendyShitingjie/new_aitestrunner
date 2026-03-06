"""参数解析器 - 支持变量引用和函数调用"""
import re
from typing import Any, Dict, List
from functions.function_registry import function_registry

class ParamResolver:
    """参数解析器
    
    支持的语法：
    1. 变量引用: ${context.batch_no} - 引用上下文中的变量
    2. 函数调用: ${uuid()} - 调用内置函数
    3. 数组引用: ${context.uids[0]} - 引用数组元素
    4. 嵌套引用: ${context.users[0].uid} - 引用嵌套对象
    """
    
    def __init__(self, context):
        """初始化参数解析器
        
        Args:
            context: ExecutionContext对象
        """
        self.context = context
        # 确保函数已加载（只需在系统启动或初始化时调用一次）
        function_registry.discover()

    
    def resolve(self, params: Any) -> Any:
        """解析参数（递归处理）
        
        Args:
            params: 参数（可以是dict、list、str等）
            
        Returns:
            解析后的参数
        """
        if isinstance(params, dict):
            return {k: self.resolve(v) for k, v in params.items()}
        elif isinstance(params, list):
            return [self.resolve(item) for item in params]
        elif isinstance(params, str):
            return self._resolve_string(params)
        else:
            return params
    
    def _resolve_string(self, value: str) -> Any:
        """解析字符串中的变量引用和函数调用
        
        支持的格式：
        - ${context.batch_no} - 引用上下文变量
        - ${uuid()} - 调用函数
        - ${context.uids[0]} - 引用数组元素
        - "prefix_${uuid()}_suffix" - 字符串拼接
        
        Args:
            value: 字符串值
            
        Returns:
            解析后的值
        """
        # 查找所有 ${...} 模式
        pattern = r'\$\{([^}]+)\}'
        matches = list(re.finditer(pattern, value))
        
        if not matches:
            return value
        
        # 如果整个字符串就是一个变量引用，直接返回值（保持原始类型）
        if len(matches) == 1 and matches[0].group(0) == value:
            expr = matches[0].group(1)
            return self._evaluate_expression(expr)
        
        # 否则进行字符串替换
        result = value
        for match in reversed(matches):  # 从后往前替换，避免索引变化
            expr = match.group(1)
            resolved_value = self._evaluate_expression(expr)
            # 转换为字符串进行替换
            result = result[:match.start()] + str(resolved_value) + result[match.end():]
        
        return result

    def _evaluate_expression(self, expr: str) -> Any:
        expr = expr.strip()

        # 处理函数调用: func_name(arg1, arg2)
        if '(' in expr and ')' in expr:
            func_name = expr.split('(')[0].strip()
            args_str = expr[expr.index('(') + 1:expr.rindex(')')].strip()

            # 从注册中心获取函数
            func = function_registry.get_function(func_name)
            if not func:
                raise ValueError(f"未知函数: {func_name}")

            if not args_str:
                return func()

            # 解析参数：支持递归解析（例如：func(${context.val})）
            # 同时也支持将逗号分隔的参数转为列表
            args = [self._resolve_string(arg.strip().strip('"\''))
                    for arg in args_str.split(',') if arg.strip()]

            return func(*args)

        # 处理上下文变量
        if expr.startswith('context.'):
            path = expr[8:]
            return self._get_context_value(path)

        return expr
    
    def _get_context_value(self, path: str) -> Any:
        """从上下文中获取值（支持嵌套路径和数组索引）
        
        Args:
            path: 路径（如 "batch_no" 或 "uids[0]" 或 "users[0].uid"）
            
        Returns:
            值
        """
        # 解析路径: batch_no 或 uids[0] 或 users[0].uid
        parts = re.split(r'\.|\[', path)

        # 从context.variables中获取第一个key的值
        first_key = parts[0]
        current = self.context.get(first_key)

        if current is None:
            raise ValueError(f"上下文中不存在变量: context.{first_key}")

        # 处理后续路径
        for part in parts[1:]:
            if not part:
                continue

            # 处理数组索引: "0]"
            if part.endswith(']'):
                index = int(part[:-1])
                current = current[index]
            else:
                # 处理对象属性
                if isinstance(current, dict):
                    current = current.get(part)
                else:
                    current = getattr(current, part, None)

            if current is None:
                raise ValueError(f"上下文中不存在路径: context.{path}")

        return current

