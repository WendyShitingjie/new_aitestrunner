"""动作库初始化

三层动作架构：
1. 通用动作层 (Generic Actions) - 高度抽象，跨业务复用
2. 业务动作层 (Business Actions) - 针对特定业务，封装业务逻辑
3. 基础设施层 (Infrastructure) - 数据库连接、HTTP客户端等
"""

# 导入注册表
from .action_registry import ActionRegistry, action_registry

# 导入并暴露自动发现功能
def discover_and_register_actions():
    """发现并注册所有动作的便利函数"""
    action_registry.discover()

# 为了向后兼容，也提供 register_all_actions 函数
def register_all_actions():
    """注册所有动作的兼容函数"""
    discover_and_register_actions()

__all__ = [
    'ActionRegistry',
    'action_registry',
    'register_all_actions',
    'discover_and_register_actions'
]
