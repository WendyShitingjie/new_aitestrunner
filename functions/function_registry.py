import importlib
import pkgutil
import os
import inspect
from typing import Callable, Dict, Any


class FunctionRegistry:
    _instance = None
    _functions: Dict[str, Callable] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FunctionRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, name: str = None):
        """装饰器：注册函数"""

        def decorator(func: Callable):
            func_name = name or func.__name__
            cls._functions[func_name] = func
            return func

        return decorator

    def get_function(self, name: str) -> Callable:
        return self._functions.get(name)

    def list_functions(self):
        return list(self._functions.keys())

    def discover(self):
        """自动发现并加载 generic 和 business 目录下的所有函数"""
        base_path = os.path.dirname(__file__)
        for sub_dir in ['generic', 'business']:
            pkg_path = os.path.join(base_path, sub_dir)
            if not os.path.exists(pkg_path):
                continue

            for _, name, _ in pkgutil.iter_modules([pkg_path]):
                full_module_name = f"functions.{sub_dir}.{name}"
                importlib.import_module(full_module_name)


# 全局单例
function_registry = FunctionRegistry()