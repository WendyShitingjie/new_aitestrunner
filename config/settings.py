"""配置管理模块"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict


class Settings:
    """配置管理类"""
    
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """加载配置文件"""
        config_path = Path(__file__).parent / "config.yaml"
        
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
        
        # 从环境变量覆盖配置
        self._override_from_env()
    
    def _override_from_env(self):
        """从环境变量覆盖配置"""
        # 数据库配置
        if os.getenv('MYSQL_HOST'):
            self._config['database']['mysql']['host'] = os.getenv('MYSQL_HOST')
        if os.getenv('MYSQL_PASSWORD'):
            self._config['database']['mysql']['password'] = os.getenv('MYSQL_PASSWORD')
        
        # AI服务配置
        if os.getenv('AI_API_KEY'):
            self._config['ai_service']['api_key'] = os.getenv('AI_API_KEY')
    
    def get(self, key: str, default=None) -> Any:
        """
        获取配置项
        
        支持点号分隔的嵌套key，例如: 'database.mysql.host'
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    @property
    def knowledge_base(self) -> Dict[str, str]:
        """知识库配置"""
        return self._config.get('knowledge_base', {})
    
    @property
    def database(self) -> Dict[str, Any]:
        """数据库配置"""
        return self._config.get('database', {})

    @property
    def http_api(self) -> Dict[str, Any]:
        """接口配置"""
        return self._config.get('http_api', {})

    @property
    def ai_service(self) -> Dict[str, Any]:
        """AI服务配置"""
        return self._config.get('ai_service', {})
    
    @property
    def execution(self) -> Dict[str, Any]:
        """执行配置"""
        return self._config.get('execution', {})


# 全局配置实例
settings = Settings()

