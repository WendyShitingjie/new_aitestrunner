"""动作注册表"""
import importlib
import pkgutil
import os
from typing import Dict, List, Type, Callable
from .base import ExecutionAction


class ActionRegistry:
    """动作注册表"""

    _instance = None
    _Actions: Dict[str, ExecutionAction] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, Action_class: Type[ExecutionAction]):
        """
        注册动作

        Args:
            Action_class: 动作类
        """
        Action = Action_class()
        self._Actions[Action.metadata.name] = Action
        return Action_class  # 返回类本身以支持装饰器模式

    def register_decorator(self, name: str = None):
        """
        装饰器：注册动作

        Args:
            name: 动作名称（可选，默认使用类的metadata.name）
        """
        def decorator(Action_class: Type[ExecutionAction]):
            # 创建实例以验证metadata是否存在
            instance = Action_class()
            action_name = name or instance.metadata.name
            # 重新注册使用正确的名称
            self._Actions[action_name] = instance
            return Action_class

        return decorator

    def get(self, name: str) -> ExecutionAction:
        """
        获取动作

        Args:
            name: 动作名称

        Returns:
            ExecutionAction: 动作实例
        """
        if name not in self._Actions:
            raise ValueError(f"动作不存在: {name}")
        return self._Actions[name]

    def list_all(self) -> List[Dict]:
        """列出所有动作"""
        return [
            {
                'name': p.metadata.name,
                'category': p.metadata.category,
                'description': p.metadata.description
            }
            for p in self._Actions.values()
        ]

    def list_by_category(self, category: str) -> List[Dict]:
        """按分类列出动作"""
        return [
            {
                'name': p.metadata.name,
                'description': p.metadata.description
            }
            for p in self._Actions.values()
            if p.metadata.category == category
        ]

    def discover(self):
        """自动发现并加载 generic 和 business 目录下的所有动作"""
        # Import specific modules directly instead of using dynamic import
        # This ensures the decorators get processed properly

        # Import all generic action modules
        try:
            import actions.generic.api_assertion
        except ImportError as e:
            print(f"Warning: 无法导入动作模块 actions.generic.api_assertion: {e}")

        try:
            import actions.generic.api_operation
        except ImportError as e:
            print(f"Warning: 无法导入动作模块 actions.generic.api_operation: {e}")

        try:
            import actions.generic.database_assertion
        except ImportError as e:
            print(f"Warning: 无法导入动作模块 actions.generic.database_assertion: {e}")

        try:
            import actions.generic.database_operation
        except ImportError as e:
            print(f"Warning: 无法导入动作模块 actions.generic.database_operation: {e}")

        try:
            import actions.generic.general_assertion
        except ImportError as e:
            print(f"Warning: 无法导入动作模块 actions.generic.general_assertion: {e}")

        try:
            import actions.generic.job_operation
        except ImportError as e:
            print(f"Warning: 无法导入动作模块 actions.generic.job_operation: {e}")

        try:
            import actions.generic.noop
        except ImportError as e:
            print(f"Warning: 无法导入动作模块 actions.generic.noop: {e}")

        try:
            import actions.generic.print
        except ImportError as e:
            print(f"Warning: 无法导入动作模块 actions.generic.print: {e}")

        try:
            import actions.generic.bridge_skill
        except ImportError as e:
            print(f"Warning: 无法导入动作模块 actions.generic.bridge_skill: {e}")

        try:
            import actions.generic.skill
        except ImportError as e:
            print(f"Warning: 无法导入动作模块 actions.generic.skill: {e}")

        # Import all business action modules
        try:
            import actions.business.datahub.data_preparation
        except ImportError as e:
            print(f"Warning: 无法导入动作模块 actions.business.datahub.data_preparation: {e}")


# 全局注册表实例
action_registry = ActionRegistry()

