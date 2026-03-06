"""执行上下文管理器"""
import copy
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import yaml


class ExecutionContext:
    """执行上下文管理器"""
    
    def __init__(self):
        self.variables: Dict[str, Dict[str, Any]] = {}  # 变量池
        self.dependencies: Dict[str, List[str]] = {}  # 依赖追踪
        self.history: List[Dict[str, Any]] = []  # 执行历史
        self.b_tree_cache: Dict[str, Any] = {}  # B树缓存
        self.a_tree_cache: Dict[str, Any] = {}  # A树缓存
    
    def set(self, key: str, value: Any, metadata: Optional[Dict] = None):
        """
        设置变量
        
        Args:
            key: 变量名
            value: 变量值
            metadata: 元数据（来源、时间戳等）
        """
        self.variables[key] = {
            'value': value,
            'metadata': metadata or {},
            'timestamp': datetime.now()
        }
        
        # 记录历史
        self.history.append({
            'action': 'set',
            'key': key,
            'value': value,
            'timestamp': datetime.now()
        })
    
    def get(self, key: str, default=None) -> Any:
        """
        获取变量，支持表达式
        
        支持:
        - 简单key: 'current_user'
        - 嵌套属性: 'current_user.user_id'
        - 模板语法: '${current_user.user_id}'
        
        Args:
            key: 变量名或表达式
            default: 默认值
        
        Returns:
            变量值
        """
        # 处理模板语法
        if isinstance(key, str) and key.startswith('${') and key.endswith('}'):
            key = key[2:-1]
        
        # 处理嵌套属性
        if '.' in key:
            parts = key.split('.')
            value = self.variables.get(parts[0], {}).get('value')
            
            for part in parts[1:]:
                if value is None:
                    return default
                
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    value = getattr(value, part, None)
            
            return value if value is not None else default
        
        # 直接获取
        var = self.variables.get(key)
        return var['value'] if var else default
    
    def track_dependency(self, step: str, depends_on: List[str]):
        """追踪依赖关系"""
        self.dependencies[step] = depends_on
    
    def get_dependency_chain(self, step: str) -> List[str]:
        """获取完整的依赖链"""
        chain = []
        to_process = [step]
        
        while to_process:
            current = to_process.pop(0)
            if current in chain:
                continue
            
            chain.append(current)
            deps = self.dependencies.get(current, [])
            to_process.extend(deps)
        
        return chain
    
    def load_b_tree(self, flow_id: str) -> Dict[str, Any]:
        """加载业务树"""
        if flow_id not in self.b_tree_cache:
            # 从知识库加载
            b_tree = self._load_from_knowledge_base('b_tree', flow_id)
            self.b_tree_cache[flow_id] = b_tree
        
        return self.b_tree_cache[flow_id]
    
    def load_a_tree(self, impl_id: str) -> Dict[str, Any]:
        """加载系统树"""
        if impl_id not in self.a_tree_cache:
            # 从知识库加载
            a_tree = self._load_from_knowledge_base('a_tree', impl_id)
            self.a_tree_cache[impl_id] = a_tree
        
        return self.a_tree_cache[impl_id]
    
    def get_from_b_tree(self, path: str) -> Any:
        """从B树获取信息"""
        # 实现略，参考前面的设计
        pass
    
    def get_from_a_tree(self, path: str) -> Any:
        """从A树获取信息"""
        # 实现略，参考前面的设计
        pass
    
    def _load_from_knowledge_base(self, tree_type: str, tree_id: str) -> Dict[str, Any]:
        """从知识库加载树"""
        # 简化实现，实际应该从配置的路径加载
        return {}
    
    def snapshot(self) -> Dict[str, Any]:
        """创建上下文快照"""
        return {
            'variables': copy.deepcopy(self.variables),
            'dependencies': copy.deepcopy(self.dependencies),
            'history': copy.deepcopy(self.history)
        }
    
    def restore(self, snapshot: Dict[str, Any]):
        """恢复上下文快照"""
        self.variables = snapshot['variables']
        self.dependencies = snapshot['dependencies']
        self.history = snapshot['history']

