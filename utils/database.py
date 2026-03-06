"""数据库连接工具"""
import pymysql
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
from config.settings import settings


class DatabaseConnection:
    """数据库连接管理类"""
    
    _connections: Dict[str, pymysql.Connection] = {}
    
    @classmethod
    def get_connection(cls, db_name: str) -> pymysql.Connection:
        """
        获取数据库连接
        
        Args:
            db_name: 数据库名称 (copilot, datahub, ares)
        
        Returns:
            pymysql.Connection: 数据库连接
        """
        if db_name not in cls._connections or not cls._connections[db_name].open:
            config = settings.database.get(db_name)
            if not config:
                raise ValueError(f"数据库配置不存在: {db_name}")
            
            cls._connections[db_name] = pymysql.connect(
                host=config['host'],
                port=config['port'],
                user=config['user'],
                password=config['password'],
                database=config['database'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
        
        return cls._connections[db_name]
    
    @classmethod
    @contextmanager
    def get_cursor(cls, db_name: str):
        """
        获取数据库游标（上下文管理器）
        
        Args:
            db_name: 数据库名称
        
        Yields:
            pymysql.cursors.DictCursor: 数据库游标
        """
        connection = cls.get_connection(db_name)
        cursor = connection.cursor()
        try:
            yield cursor
            connection.commit()
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            cursor.close()
    
    @classmethod
    def execute_query(cls, db_name: str, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        执行查询SQL
        
        Args:
            db_name: 数据库名称
            sql: SQL语句
            params: 参数
        
        Returns:
            List[Dict]: 查询结果
        """
        with cls.get_cursor(db_name) as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    
    @classmethod
    def execute_update(cls, db_name: str, sql: str, params: Optional[tuple] = None) -> int:
        """
        执行更新SQL
        
        Args:
            db_name: 数据库名称
            sql: SQL语句
            params: 参数
        
        Returns:
            int: 影响的行数
        """
        with cls.get_cursor(db_name) as cursor:
            affected_rows = cursor.execute(sql, params)
            return affected_rows
    
    @classmethod
    def close_all(cls):
        """关闭所有数据库连接"""
        for conn in cls._connections.values():
            if conn.open:
                conn.close()
        cls._connections.clear()


def parse_table_name(full_table_name: str) -> tuple[str, str]:
    """
    解析表名，提取数据库名和表名
    
    Args:
        full_table_name: 完整表名 (如 copilot.ai_script_recommendation_log)
    
    Returns:
        tuple: (数据库名, 表名)
    """
    if '.' in full_table_name:
        db_name, table_name = full_table_name.split('.', 1)
        return db_name, table_name
    else:
        # 默认使用copilot数据库
        return 'copilot', full_table_name

