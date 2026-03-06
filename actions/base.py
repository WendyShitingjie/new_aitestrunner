"""动作基类"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ActionMetadata(BaseModel):
    """动作元数据"""
    name: str  # 动作名称
    category: str  # 分类: data, api, assertion, mq, cache, business
    description: str  # 描述
    parameters: List[Dict[str, Any]]  # 参数定义
    returns: Dict[str, str]  # 返回值定义
    examples: List[Dict[str, str]] = []  # 使用示例
    related_business_rules: List[str] = []  # 关联的业务规则
    related_data_models: List[str] = []  # 关联的数据模型


class ExecutionAction(ABC):
    """执行动作基类"""
    
    # 子类需要定义metadata
    metadata: ActionMetadata = None
    
    def __init__(self):
        """初始化动作"""
        if self.metadata is None:
            raise NotImplementedError("子类必须定义metadata")
    
    @abstractmethod
    def execute(self, context, **params) -> Any:
        """
        执行动作
        
        Args:
            context: 执行上下文
            **params: 参数
        
        Returns:
            执行结果
        """
        pass
    
    def get_required_parameters(self) -> List[str]:
        """获取必填参数列表"""
        return [
            p['name'] for p in self.metadata.parameters
            if p.get('required', False)
        ]
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """验证参数"""
        required = self.get_required_parameters()
        for param in required:
            if param not in params:
                raise ValueError(f"缺少必填参数: {param}")
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取元数据"""
        return self.metadata.dict()

