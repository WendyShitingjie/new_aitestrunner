#!/usr/bin/env python3
"""
JDBC Warehouse Test Skill - 表结构读取器
用于从数据库读取表结构和元数据信息
"""
import pymysql
import os
import configparser


class TableReader:
    """表结构读取器"""

    def __init__(self, config_file=None):
        """
        初始化读取器

        Args:
            config_file: 数据库配置文件路径（可选）
        """
        # 加载数据库配置
        self.environments = self._load_environments_from_config(config_file)

    def _load_environments_from_config(self, config_file=None):
        """从配置文件加载测试环境"""
        if config_file is None:
            # 默认配置文件路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_file = os.path.join(script_dir, 'db_config.ini')

        if not os.path.exists(config_file):
            print(f"警告: 配置文件不存在: {config_file}")
            return {}

        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')

        environments = {}
        for section in config.sections():
            environments[section] = {
                'type': config.get(section, 'type'),
                'host': config.get(section, 'host'),
                'port': config.getint(section, 'port'),
                'database': config.get(section, 'database'),
                'username': config.get(section, 'username'),
                'password': config.get(section, 'password'),
                'description': config.get(section, 'description', fallback='')
            }

        return environments

    def get_table_info(self, database, table, env=None, **conn_params):
        """
        获取表的完整信息

        Args:
            database: 数据库名
            table: 表名
            env: 环境名（可选，如 adb-realtime）
            **conn_params: 直接的数据库连接参数（host, port, user, password）

        Returns:
            dict: 表信息，包含：
                - database: 数据库名
                - table: 表名
                - columns: 字段列表
                - primary_key: 主键字段
                - instance: 实例名
                - db_type: 数据源类型
        """
        connection = None
        try:
            # 获取数据库连接
            if env and env in self.environments:
                env_config = self.environments[env]
                connection = pymysql.connect(
                    host=env_config['host'],
                    port=env_config['port'],
                    user=env_config['username'],
                    password=env_config['password'],
                    database=database,
                    charset='utf8mb4'
                )
                db_type = env_config['type']
                instance = env
            elif conn_params:
                connection = pymysql.connect(
                    host=conn_params.get('host'),
                    port=conn_params.get('port', 3306),
                    user=conn_params.get('user'),
                    password=conn_params.get('password', ''),
                    database=database,
                    charset='utf8mb4'
                )
                db_type = conn_params.get('db_type', 'mysql')
                instance = conn_params.get('instance', database)
            else:
                raise ValueError("必须提供 env 或数据库连接参数")

            cursor = connection.cursor()

            # 检查表是否存在
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            if not cursor.fetchone():
                raise ValueError(f"表 {table} 不存在于数据库 {database}")

            # 获取表结构
            cursor.execute(f"DESCRIBE {table}")
            columns = []
            primary_key = None

            for row in cursor.fetchall():
                field_name = row[0]
                field_type = row[1]
                is_nullable = row[2]
                key = row[3]
                default = row[4]

                columns.append({
                    'name': field_name,
                    'type': field_type,
                    'nullable': is_nullable,
                    'key': key,
                    'default': default
                })

                if key == 'PRI':
                    primary_key = field_name

            # 获取表注释
            cursor.execute(f"""
                SELECT TABLE_COMMENT
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = '{database}'
                AND TABLE_NAME = '{table}'
            """)
            table_comment = cursor.fetchone()
            table_comment = table_comment[0] if table_comment else ''

            cursor.close()
            connection.close()

            return {
                'database': database,
                'table': table,
                'columns': columns,
                'primary_key': primary_key or 'id',
                'instance': instance,
                'db_type': db_type,
                'table_comment': table_comment
            }

        except Exception as e:
            if connection:
                connection.close()
            raise RuntimeError(f"读取表结构失败: {str(e)}")

    def has_time_fields(self, table_info):
        """
        检查表是否有标准时间字段

        Args:
            table_info: 表信息（来自 get_table_info）

        Returns:
            dict: {'has_created': bool, 'has_updated': bool,
                  'created_field': str, 'updated_field': str}
        """
        created_field = None
        updated_field = None

        for col in table_info['columns']:
            col_name = col['name'].lower()
            if 'created' in col_name and 'at' in col_name:
                created_field = col['name']
            elif 'updated' in col_name and 'at' in col_name:
                updated_field = col['name']

        return {
            'has_created': created_field is not None,
            'has_updated': updated_field is not None,
            'created_field': created_field or 'created_at',
            'updated_field': updated_field or 'updated_at'
        }

    def verify_metadata_exists(self, instance, database, table):
        """
        验证元数据是否已完善

        Args:
            instance: 实例名
            database: 数据库名
            table: 表名

        Returns:
            bool: 元数据是否存在
        """
        # 连接 dataops 库查询元数据
        try:
            connection = pymysql.connect(
                host='bigdata-biz.db.ali-bj-bdsit01.shuheo.net',
                port=3306,
                user='bdsit_user_0e0bc33',
                password='bdsit_user_0e0bc33_26587a',
                database='dataops',
                charset='utf8mb4'
            )

            cursor = connection.cursor()
            cursor.execute(f"""
                SELECT COUNT(*)
                FROM dataops_extract_input_datasource_config_info
                WHERE instance_name = '{instance}'
                AND db_name = '{database}'
                AND table_name = '{table}'
                AND status != 'DELETED'
            """)

            count = cursor.fetchone()[0]
            cursor.close()
            connection.close()

            return count > 0

        except Exception as e:
            print(f"警告: 无法验证元数据: {str(e)}")
            return False


def main():
    """测试函数"""
    import sys

    if len(sys.argv) < 3:
        print("用法: python table_reader.py <database> <table> [env]")
        sys.exit(1)

    database = sys.argv[1]
    table = sys.argv[2]
    env = sys.argv[3] if len(sys.argv) > 3 else None

    reader = TableReader()

    try:
        print(f"正在读取表结构: {database}.{table}")
        table_info = reader.get_table_info(database, table, env=env)

        print("\n表信息:")
        print(f"  数据库: {table_info['database']}")
        print(f"  表名: {table_info['table']}")
        print(f"  实例: {table_info['instance']}")
        print(f"  类型: {table_info['db_type']}")
        print(f"  主键: {table_info['primary_key']}")
        print(f"  字段数: {len(table_info['columns'])}")

        time_fields = reader.has_time_fields(table_info)
        print(f"\n时间字段:")
        print(f"  创建时间: {time_fields['created_field']} ({'存在' if time_fields['has_created'] else '不存在'})")
        print(f"  更新时间: {time_fields['updated_field']} ({'存在' if time_fields['has_updated'] else '不存在'})")

        # 验证元数据
        metadata_exists = reader.verify_metadata_exists(
            table_info['instance'],
            table_info['database'],
            table_info['table']
        )
        print(f"\n元数据状态: {'已完善' if metadata_exists else '未完善'}")

    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
