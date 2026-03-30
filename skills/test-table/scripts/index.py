#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试表生成器 - 支持 MySQL、TiDB、ADB 等 JDBC 数据库
可以在 PyCharm 中直接运行，也可以作为 Claude Code skill 使用
"""

import sys
import json
import random
import string
import os
import configparser
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

try:
    from generate_invalid_comment_tables import InvalidCommentTableGenerator
except ImportError:
    InvalidCommentTableGenerator = None


class TestTableGenerator:
    """测试表生成器类"""

    @classmethod
    def load_environments_from_config(cls, config_file: str = None) -> Dict[str, Dict[str, Any]]:
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

    # 预配置的测试环境（从配置文件加载）
    TEST_ENVIRONMENTS = {}

    # 数据库类型配置
    DB_CONFIGS = {
        'mysql': {
            'driver': 'com.mysql.cj.jdbc.Driver',
            'url_template': 'jdbc:mysql://{host}:{port}/{database}?useSSL=false&serverTimezone=UTC',
            'default_port': 3306
        },
        'tidb': {
            'driver': 'com.mysql.cj.jdbc.Driver',
            'url_template': 'jdbc:mysql://{host}:{port}/{database}?useSSL=false&serverTimezone=UTC',
            'default_port': 4000
        },
        'adb': {
            'driver': 'com.mysql.cj.jdbc.Driver',
            'url_template': 'jdbc:mysql://{host}:{port}/{database}?useSSL=false',
            'default_port': 3306
        }
    }

    # 数据类型映射（符合 MySQL 建表规范）
    # 格式：(字段名, 数据类型, 约束, 注释)
    ADB_DATA_TYPE_SCHEMAS = {
        'string': [
            ('id', 'BIGINT', 'NOT NULL AUTO_INCREMENT', '主键ID'),
            ('user_name', 'VARCHAR(100)', 'NOT NULL DEFAULT \'\'', '用户姓名'),
            ('email', 'VARCHAR(255)', 'NOT NULL DEFAULT \'\'', '电子邮箱'),
            ('description', 'TEXT', '', '详细描述'),
            ('created_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP', '创建时间'),
            ('updated_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', '更新时间'),
            ('PRIMARY KEY', 'id', '', ''),
            ('KEY', 'idx_updated_at', 'updated_at', '')
        ],
        'number': [
            ('id', 'BIGINT', 'NOT NULL AUTO_INCREMENT', '主键ID'),
            ('int_value', 'INT', 'NOT NULL DEFAULT 0', '整数值'),
            ('bigint_value', 'BIGINT', 'NOT NULL DEFAULT 0', '长整数值'),
            ('decimal_value', 'DECIMAL(10,2)', 'NOT NULL DEFAULT 0.00', '小数值'),
            ('price', 'DECIMAL(7,5)', 'DEFAULT NULL', '价格'),
            ('amount', 'DECIMAL(15,4)', 'DEFAULT NULL', '金额'),
            ('rate', 'DECIMAL(5,2)', 'DEFAULT NULL', '比率'),
            ('float_value', 'FLOAT', 'NOT NULL DEFAULT 0.0', '浮点数值'),
            ('created_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP', '创建时间'),
            ('updated_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', '更新时间'),
            ('PRIMARY KEY', 'id', '', ''),
            ('KEY', 'idx_updated_at', 'updated_at', '')
        ],
        'date': [
            ('id', 'BIGINT', 'NOT NULL AUTO_INCREMENT', '主键ID'),
            ('date_value', 'DATE', 'NOT NULL', '日期值'),
            ('datetime_value', 'DATETIME', 'DEFAULT NULL', '日期时间值'),
            ('timestamp_value', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP', '时间戳值'),
            ('year_value', 'YEAR', 'DEFAULT NULL', '年份值'),
            ('created_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP', '创建时间'),
            ('updated_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', '更新时间'),
            ('PRIMARY KEY', 'id', '', ''),
            ('KEY', 'idx_updated_at', 'updated_at', '')
        ],
        'boolean': [
            ('id', 'BIGINT', 'NOT NULL AUTO_INCREMENT', '主键ID'),
            ('is_active', 'TINYINT', 'NOT NULL DEFAULT 1', '是否激活'),
            ('is_deleted', 'TINYINT', 'NOT NULL DEFAULT 0', '是否删除'),
            ('is_verified', 'TINYINT', 'NOT NULL DEFAULT 0', '是否验证'),
            ('created_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP', '创建时间'),
            ('updated_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', '更新时间'),
            ('PRIMARY KEY', 'id', '', ''),
            ('KEY', 'idx_updated_at', 'updated_at', '')
        ],
        'mixed': [
            ('id', 'BIGINT', 'NOT NULL AUTO_INCREMENT', '主键ID'),
            ('user_name', 'VARCHAR(100)', 'NOT NULL DEFAULT \'\'', '用户姓名'),
            ('age', 'INT', 'NOT NULL DEFAULT 0', '年龄'),
            ('salary', 'DECIMAL(10,2)', 'NOT NULL DEFAULT 0.00', '薪资'),
            ('birth_date', 'DATE', 'DEFAULT NULL', '出生日期'),
            ('is_active', 'TINYINT', 'NOT NULL DEFAULT 1', '是否激活'),
            ('description', 'TEXT', '', '详细描述'),
            ('created_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP', '创建时间'),
            ('updated_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', '更新时间'),
            ('PRIMARY KEY', 'id', '', ''),
            ('KEY', 'idx_updated_at', 'updated_at', '')
        ],
        'composite_key': [
            ('user_id', 'BIGINT', 'NOT NULL', '用户ID'),
            ('order_id', 'BIGINT', 'NOT NULL', '订单ID'),
            ('product_id', 'BIGINT', 'NOT NULL', '商品ID'),
            ('quantity', 'INT', 'NOT NULL DEFAULT 0', '数量'),
            ('amount', 'DECIMAL(10,2)', 'NOT NULL DEFAULT 0.00', '金额'),
            ('status', 'TINYINT', 'NOT NULL DEFAULT 0', '状态'),
            ('created_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP', '创建时间'),
            ('updated_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', '更新时间'),
            ('PRIMARY KEY', 'user_id, order_id', '', ''),
            ('KEY', 'idx_updated_at', 'updated_at', '')
        ]
    }

    DATA_TYPE_SCHEMAS = {
        'string': [
            ('id', 'BIGINT UNSIGNED', 'NOT NULL AUTO_INCREMENT', '主键ID'),
            ('user_name', 'VARCHAR(100)', 'NOT NULL DEFAULT \'\'', '用户姓名'),
            ('email', 'VARCHAR(255)', 'NOT NULL DEFAULT \'\'', '电子邮箱'),
            ('description', 'TEXT', '', '详细描述'),
            ('created_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP', '创建时间'),
            ('updated_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', '更新时间'),
            ('PRIMARY KEY', 'id', '', ''),
            ('KEY', 'idx_updated_at', 'updated_at', '')
        ],
        'number': [
            ('id', 'BIGINT UNSIGNED', 'NOT NULL AUTO_INCREMENT', '主键ID'),
            ('int_value', 'INT', 'NOT NULL DEFAULT 0', '整数值'),
            ('bigint_value', 'BIGINT', 'NOT NULL DEFAULT 0', '长整数值'),
            ('decimal_value', 'DECIMAL(10,2)', 'NOT NULL DEFAULT 0.00', '小数值'),
            ('price', 'DECIMAL(7,5)', 'DEFAULT NULL', '价格'),
            ('amount', 'DECIMAL(15,4)', 'DEFAULT NULL', '金额'),
            ('rate', 'DECIMAL(5,2)', 'DEFAULT NULL', '比率'),
            ('float_value', 'FLOAT', 'NOT NULL DEFAULT 0.0', '浮点数值'),
            ('created_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP', '创建时间'),
            ('updated_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', '更新时间'),
            ('PRIMARY KEY', 'id', '', ''),
            ('KEY', 'idx_updated_at', 'updated_at', '')
        ],
        'date': [
            ('id', 'BIGINT UNSIGNED', 'NOT NULL AUTO_INCREMENT', '主键ID'),
            ('date_value', 'DATE', 'NOT NULL', '日期值'),
            ('datetime_value', 'DATETIME', 'DEFAULT NULL', '日期时间值'),
            ('timestamp_value', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP', '时间戳值'),
            ('year_value', 'YEAR', 'DEFAULT NULL', '年份值'),
            ('created_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP', '创建时间'),
            ('updated_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', '更新时间'),
            ('PRIMARY KEY', 'id', '', ''),
            ('KEY', 'idx_updated_at', 'updated_at', '')
        ],
        'boolean': [
            ('id', 'BIGINT UNSIGNED', 'NOT NULL AUTO_INCREMENT', '主键ID'),
            ('is_active', 'TINYINT', 'NOT NULL DEFAULT 1', '是否激活'),
            ('is_deleted', 'TINYINT', 'NOT NULL DEFAULT 0', '是否删除'),
            ('is_verified', 'TINYINT', 'NOT NULL DEFAULT 0', '是否验证'),
            ('created_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP', '创建时间'),
            ('updated_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', '更新时间'),
            ('PRIMARY KEY', 'id', '', ''),
            ('KEY', 'idx_updated_at', 'updated_at', '')
        ],
        'mixed': [
            ('id', 'BIGINT UNSIGNED', 'NOT NULL AUTO_INCREMENT', '主键ID'),
            ('user_name', 'VARCHAR(100)', 'NOT NULL DEFAULT \'\'', '用户姓名'),
            ('age', 'INT', 'NOT NULL DEFAULT 0', '年龄'),
            ('salary', 'DECIMAL(10,2)', 'NOT NULL DEFAULT 0.00', '薪资'),
            ('birth_date', 'DATE', 'DEFAULT NULL', '出生日期'),
            ('is_active', 'TINYINT', 'NOT NULL DEFAULT 1', '是否激活'),
            ('description', 'TEXT', '', '详细描述'),
            ('created_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP', '创建时间'),
            ('updated_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', '更新时间'),
            ('PRIMARY KEY', 'id', '', ''),
            ('KEY', 'idx_updated_at', 'updated_at', '')
        ],
        'composite_key': [
            ('user_id', 'BIGINT UNSIGNED', 'NOT NULL', '用户ID'),
            ('order_id', 'BIGINT UNSIGNED', 'NOT NULL', '订单ID'),
            ('product_id', 'BIGINT UNSIGNED', 'NOT NULL', '商品ID'),
            ('quantity', 'INT', 'NOT NULL DEFAULT 0', '数量'),
            ('amount', 'DECIMAL(10,2)', 'NOT NULL DEFAULT 0.00', '金额'),
            ('status', 'TINYINT', 'NOT NULL DEFAULT 0', '状态'),
            ('created_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP', '创建时间'),
            ('updated_at', 'TIMESTAMP', 'NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', '更新时间'),
            ('PRIMARY KEY', 'user_id, order_id', '', ''),
            ('KEY', 'idx_updated_at', 'updated_at', '')
        ]
    }

    def __init__(self, db_type: str = 'mysql'):
        """初始化生成器"""
        if db_type not in self.DB_CONFIGS:
            raise ValueError(f"不支持的数据库类型: {db_type}，支持的类型: {list(self.DB_CONFIGS.keys())}")
        self.db_type = db_type
        self.db_config = self.DB_CONFIGS[db_type]
        
        if db_type == 'adb':
            self.data_type_schemas = self.ADB_DATA_TYPE_SCHEMAS
        else:
            self.data_type_schemas = self.DATA_TYPE_SCHEMAS

    def generate_create_table_sql(self, table_name: str, data_type: str, table_comment: str = '') -> str:
        """生成建表 SQL（符合 MySQL 建表规范）"""
        if data_type not in self.data_type_schemas:
            raise ValueError(f"不支持的数据类型: {data_type}，支持的类型: {list(self.data_type_schemas.keys())}")

        schema = self.data_type_schemas[data_type]
        columns = []
        keys = []

        for col_name, col_type, col_constraint, col_comment in schema:
            # 处理主键定义
            if col_name == 'PRIMARY KEY':
                keys.append(f"    PRIMARY KEY ({col_type})")
            # 处理索引定义
            elif col_name == 'KEY':
                keys.append(f"    KEY {col_type} ({col_constraint})")
            # 处理普通字段
            else:
                col_def = f"    {col_name} {col_type}"
                if col_constraint:
                    col_def += f" {col_constraint}"
                if col_comment:
                    col_def += f" COMMENT '{col_comment}'"
                columns.append(col_def)

        # 组合所有定义
        all_definitions = columns + keys

        # 生成表注释
        if not table_comment:
            table_comment = f'{table_name}测试表'

        sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
        sql += ",\n".join(all_definitions)
        sql += f"\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='{table_comment}';"

        return sql

    def generate_random_string(self, length: int = 10) -> str:
        """生成随机字符串"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def generate_random_email(self) -> str:
        """生成随机邮箱"""
        username = self.generate_random_string(8)
        domains = ['example.com', 'test.com', 'demo.com']
        return f"{username}@{random.choice(domains)}"

    def generate_random_date(self, start_year: int = 2020, end_year: int = 2024) -> str:
        """生成随机日期"""
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)
        delta = end_date - start_date
        random_days = random.randint(0, delta.days)
        random_date = start_date + timedelta(days=random_days)
        return random_date.strftime('%Y-%m-%d')

    def generate_random_datetime(self) -> str:
        """生成随机日期时间"""
        date = self.generate_random_date()
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        return f"{date} {hour:02d}:{minute:02d}:{second:02d}"

    def generate_test_data(self, data_type: str, row_count: int) -> List[Dict[str, Any]]:
        """生成测试数据"""
        if data_type not in self.data_type_schemas:
            raise ValueError(f"不支持的数据类型: {data_type}")

        schema = self.data_type_schemas[data_type]
        data = []

        for i in range(row_count):
            row = {}
            for col_name, col_type, col_constraint, col_comment in schema:
                # 跳过主键、索引定义和自动生成的字段
                if col_name in ['PRIMARY KEY', 'KEY']:
                    continue
                if 'AUTO_INCREMENT' in col_constraint:
                    continue
                if 'DEFAULT CURRENT_TIMESTAMP' in col_constraint:
                    continue
                if 'DEFAULT NULL' in col_constraint:
                    # 对于可为 NULL 的字段，随机决定是否生成值
                    if random.random() < 0.3:
                        continue

                # 根据字段类型生成数据
                if 'VARCHAR' in col_type:
                    if 'email' in col_name:
                        row[col_name] = self.generate_random_email()
                    elif 'password' in col_name:
                        row[col_name] = 'test_' + self.generate_random_string(16)
                    else:
                        row[col_name] = self.generate_random_string(random.randint(5, 20))
                elif col_type == 'TEXT':
                    row[col_name] = self.generate_random_string(random.randint(50, 200))
                elif col_type == 'JSON':
                    # 生成 JSON 数据
                    json_data = {
                        'key1': self.generate_random_string(10),
                        'key2': random.randint(1, 100),
                        'key3': random.choice([True, False])
                    }
                    row[col_name] = json.dumps(json_data, ensure_ascii=False)
                elif 'BIGINT' in col_type:
                    row[col_name] = random.randint(1000, 999999)
                elif col_type == 'INT':
                    row[col_name] = random.randint(1, 100)
                elif 'DECIMAL' in col_type:
                    # 解析 DECIMAL(M,D) 中的精度
                    import re
                    match = re.search(r'DECIMAL\((\d+),(\d+)\)', col_type)
                    if match:
                        precision = int(match.group(1))
                        scale = int(match.group(2))
                        # 生成符合精度的随机数
                        max_value = 10 ** (precision - scale) - 1
                        random_value = random.uniform(0, max_value)
                        row[col_name] = round(random_value, scale)
                    else:
                        row[col_name] = round(random.uniform(1000, 99999), 2)
                elif col_type == 'FLOAT':
                    row[col_name] = round(random.uniform(1, 1000), 2)
                elif col_type == 'DATE':
                    row[col_name] = self.generate_random_date()
                elif col_type == 'DATETIME':
                    row[col_name] = self.generate_random_datetime()
                elif col_type == 'YEAR':
                    row[col_name] = random.randint(2020, 2024)
                elif col_type == 'TINYINT':
                    row[col_name] = random.choice([0, 1])

            data.append(row)

        return data

    def generate_insert_sql(self, table_name: str, data: List[Dict[str, Any]]) -> List[str]:
        """生成插入数据的 SQL"""
        if not data:
            return []

        sql_statements = []
        for row in data:
            columns = list(row.keys())
            values = []
            for col in columns:
                val = row[col]
                if isinstance(val, bool):
                    values.append('1' if val else '0')
                elif isinstance(val, (int, float)):
                    values.append(str(val))
                elif val is None:
                    values.append('NULL')
                else:
                    escaped_val = str(val).replace("'", "''").replace("\\", "\\\\")
                    values.append(f"'{escaped_val}'")

            sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});"
            sql_statements.append(sql)

        return sql_statements

    def generate_connection_info(self, host: str = 'localhost', port: int = None,
                                 database: str = 'test', username: str = 'root',
                                 password: str = '') -> Dict[str, str]:
        """生成数据库连接信息"""
        if port is None:
            port = self.db_config['default_port']

        jdbc_url = self.db_config['url_template'].format(
            host=host,
            port=port,
            database=database
        )

        return {
            'driver': self.db_config['driver'],
            'url': jdbc_url,
            'username': username,
            'password': password,
            'database_type': self.db_type
        }

    def generate_full_script(self, table_name: str, data_type: str, row_count: int,
                            include_drop: bool = False, table_comment: str = '') -> str:
        """生成完整的 SQL 脚本"""
        script_lines = []

        script_lines.append(f"-- 测试表生成脚本")
        script_lines.append(f"-- 数据库类型: {self.db_type}")
        script_lines.append(f"-- 表名: {table_name}")
        script_lines.append(f"-- 数据类型: {data_type}")
        script_lines.append(f"-- 数据行数: {row_count}")
        script_lines.append(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        script_lines.append(f"-- 符合 MySQL 建表规范")
        script_lines.append("")

        if include_drop:
            script_lines.append(f"DROP TABLE IF EXISTS {table_name};")
            script_lines.append("")

        create_sql = self.generate_create_table_sql(table_name, data_type, table_comment)
        script_lines.append(create_sql)
        script_lines.append("")

        test_data = self.generate_test_data(data_type, row_count)
        insert_sqls = self.generate_insert_sql(table_name, test_data)

        for sql in insert_sqls:
            script_lines.append(sql)

        return "\n".join(script_lines)

    def execute_sql(self, sql_script: str, env_name: str = None,
                   host: str = None, port: int = None, database: str = None,
                   username: str = None, password: str = None) -> Dict[str, Any]:
        """执行 SQL 脚本到数据库"""
        try:
            import pymysql
        except ImportError:
            return {
                'success': False,
                'error': '需要安装 pymysql 库: pip install pymysql'
            }

        # 如果指定了环境名称，使用预配置的环境
        if env_name:
            if env_name not in self.TEST_ENVIRONMENTS:
                return {
                    'success': False,
                    'error': f'未找到环境配置: {env_name}，可用环境: {list(self.TEST_ENVIRONMENTS.keys())}'
                }
            env = self.TEST_ENVIRONMENTS[env_name]
            host = env['host']
            port = env['port']
            database = env['database']
            username = env['username']
            password = env['password']
        else:
            # 使用自定义连接信息
            if not all([host, database, username]):
                return {
                    'success': False,
                    'error': '必须提供 host, database, username 参数或指定 env_name'
                }
            if port is None:
                port = self.db_config['default_port']

        try:
            # 连接数据库
            connection = pymysql.connect(
                host=host,
                port=port,
                user=username,
                password=password or '',
                database=database,
                charset='utf8mb4'
            )

            cursor = connection.cursor()

            # 更智能的 SQL 分割：处理多行语句
            sql_statements = []
            current_statement = []

            for line in sql_script.split('\n'):
                line = line.strip()
                # 跳过注释行
                if line.startswith('--') or not line:
                    continue

                current_statement.append(line)

                # 如果行以分号结尾，表示一条完整的 SQL 语句
                if line.endswith(';'):
                    full_sql = ' '.join(current_statement)
                    sql_statements.append(full_sql.rstrip(';'))
                    current_statement = []

            executed_count = 0
            for sql in sql_statements:
                if sql.strip():
                    cursor.execute(sql)
                    executed_count += 1

            connection.commit()
            cursor.close()
            connection.close()

            return {
                'success': True,
                'executed_count': executed_count,
                'host': host,
                'database': database,
                'message': f'成功执行 {executed_count} 条 SQL 语句'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'host': host,
                'database': database
            }

    @classmethod
    def list_environments(cls) -> List[Dict[str, str]]:
        """列出所有预配置的测试环境"""
        envs = []
        for name, config in cls.TEST_ENVIRONMENTS.items():
            envs.append({
                'name': name,
                'type': config['type'],
                'host': config['host'],
                'database': config['database'],
                'description': config['description']
            })
        return envs


def main():
    """主函数 - 用于 Claude Code skill 调用和独立运行"""
    import argparse

    # 加载配置文件中的环境
    TestTableGenerator.TEST_ENVIRONMENTS = TestTableGenerator.load_environments_from_config()

    parser = argparse.ArgumentParser(description='测试表生成器 - 支持 MySQL、TiDB、ADB')

    # 添加子命令
    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # 列出环境命令
    list_parser = subparsers.add_parser('list-envs', help='列出所有预配置的测试环境')

    # 复制表命令
    copy_parser = subparsers.add_parser('copy-table', help='复制表结构')
    copy_parser.add_argument('--sourceTable', required=True, help='源表名称')
    copy_parser.add_argument('--targetTable', required=False, help='目标表名称（可选，如不提供将自动生成：源表名_MMDD_序号）')
    copy_parser.add_argument('--env', help='使用预配置的测试环境')
    copy_parser.add_argument('--copyData', action='store_true', help='同时复制数据')
    copy_parser.add_argument('--showDDL', action='store_true', help='显示表 DDL')
    copy_parser.add_argument('--host', help='数据库主机')
    copy_parser.add_argument('--port', type=int, help='数据库端口')
    copy_parser.add_argument('--database', help='数据库名称')
    copy_parser.add_argument('--username', help='用户名')
    copy_parser.add_argument('--password', default='', help='密码')

    # 生成表命令
    generate_parser = subparsers.add_parser('generate', help='生成测试表 SQL')
    generate_parser.add_argument('--dbType', default='mysql', choices=['mysql', 'tidb', 'adb'],
                       help='数据库类型 (默认: mysql)')
    generate_parser.add_argument('--tableName', required=True, help='表名称')
    generate_parser.add_argument('--dataType', default='mixed',
                       choices=['string', 'number', 'date', 'boolean', 'mixed', 'composite_key'],
                       help='数据类型 (默认: mixed)')
    generate_parser.add_argument('--rowCount', type=int, default=10, help='生成的测试数据行数 (默认: 10)')
    generate_parser.add_argument('--tableComment', default='', help='表注释 (可选)')
    generate_parser.add_argument('--output', help='输出 SQL 文件路径 (可选)')
    generate_parser.add_argument('--includeDrop', action='store_true', help='是否包含 DROP TABLE 语句')
    generate_parser.add_argument('--execute', action='store_true', help='直接执行到数据库')
    generate_parser.add_argument('--env', help='使用预配置的测试环境 (如: cjjcommon, tidb-ares)')
    generate_parser.add_argument('--showConnection', action='store_true', help='显示 JDBC 连接信息')
    generate_parser.add_argument('--host', help='数据库主机')
    generate_parser.add_argument('--port', type=int, help='数据库端口')
    generate_parser.add_argument('--database', help='数据库名称')
    generate_parser.add_argument('--username', help='用户名')
    generate_parser.add_argument('--password', default='', help='密码')
    generate_parser.add_argument('--invalidScenario',
                       choices=['table_no_chinese', 'table_short', 'field_no_chinese', 'field_short'],
                       help='异常场景类型（用于生成违反规范的测试表）')

    # 兼容旧版本：如果没有子命令，默认为 generate
    args, unknown = parser.parse_known_args()
    if args.command is None:
        # 重新解析为 generate 命令
        sys.argv.insert(1, 'generate')
        args = parser.parse_args()

    # 列出环境
    if args.command == 'list-envs':
        envs = TestTableGenerator.list_environments()
        print(f"\n{'='*80}")
        print(f"预配置的测试环境")
        print(f"{'='*80}")
        for env in envs:
            print(f"\n环境名称: {env['name']}")
            print(f"  类型: {env['type']}")
            print(f"  主机: {env['host']}")
            print(f"  数据库: {env['database']}")
            print(f"  说明: {env['description']}")
        print(f"\n{'='*80}\n")
        return

    # 复制表
    if args.command == 'copy-table':
        try:
            import pymysql
        except ImportError:
            print("\n✗ 需要安装 pymysql 库: pip install pymysql\n")
            sys.exit(1)

        # 获取数据库连接信息
        if args.env:
            if args.env not in TestTableGenerator.TEST_ENVIRONMENTS:
                print(f"\n✗ 未找到环境配置: {args.env}")
                print(f"可用环境: {list(TestTableGenerator.TEST_ENVIRONMENTS.keys())}\n")
                sys.exit(1)
            env = TestTableGenerator.TEST_ENVIRONMENTS[args.env]
            host = env['host']
            port = env['port']
            database = env['database']
            username = env['username']
            password = env['password']
        else:
            if not all([args.host, args.database, args.username]):
                print("\n✗ 必须提供 --env 或 (--host, --database, --username) 参数\n")
                sys.exit(1)
            host = args.host
            port = args.port or 3306
            database = args.database
            username = args.username
            password = args.password

        try:
            # 连接数据库（需要先连接才能检查表是否存在）
            connection = pymysql.connect(
                host=host,
                port=port,
                user=username,
                password=password or '',
                database=database,
                charset='utf8mb4'
            )
            cursor = connection.cursor()

            # 如果没有提供目标表名，自动生成
            target_table = args.targetTable
            if not target_table:
                from datetime import datetime
                date_suffix = datetime.now().strftime('%m%d')
                base_target = f"{args.sourceTable}_{date_suffix}"

                # 检查是否已存在同名表
                cursor.execute(f"SHOW TABLES LIKE '{base_target}'")
                if cursor.fetchone():
                    # 已存在，添加序号后缀
                    seq = 1
                    while True:
                        target_table = f"{base_target}_{seq:02d}"
                        cursor.execute(f"SHOW TABLES LIKE '{target_table}'")
                        if not cursor.fetchone():
                            break
                        seq += 1
                else:
                    target_table = base_target

                print(f"✓ 自动生成目标表名: {target_table}")

            print(f"\n{'='*60}")
            print(f"复制表结构")
            print(f"{'='*60}")
            print(f"源表: {args.sourceTable}")
            print(f"目标表: {target_table}")
            print(f"主机: {host}")
            print(f"数据库: {database}")
            print(f"{'='*60}\n")

            # 获取源表的 DDL
            cursor.execute(f"SHOW CREATE TABLE {args.sourceTable}")
            result = cursor.fetchone()
            if not result:
                print(f"\n✗ 未找到表: {args.sourceTable}\n")
                sys.exit(1)

            create_ddl = result[1]

            # 替换表名（支持不同的大小写格式）
            import re
            # 匹配 CREATE TABLE 或 Create Table 等各种大小写组合
            pattern = re.compile(
                rf"(CREATE\s+TABLE|Create\s+Table)\s+`{re.escape(args.sourceTable)}`",
                re.IGNORECASE
            )
            new_ddl = pattern.sub(rf"\1 `{target_table}`", create_ddl, count=1)

            if args.showDDL:
                print("源表 DDL:")
                print("-" * 60)
                print(create_ddl)
                print("-" * 60)
                print("\n新表 DDL:")
                print("-" * 60)
                print(new_ddl)
                print("-" * 60)
                print()

            # 执行建表语句
            cursor.execute(new_ddl)
            connection.commit()
            print(f"✓ 表结构复制成功: {target_table}")

            # 如果需要复制数据
            if args.copyData:
                print(f"\n正在复制数据...")
                cursor.execute(f"INSERT INTO {target_table} SELECT * FROM {args.sourceTable}")
                connection.commit()
                affected_rows = cursor.rowcount
                print(f"✓ 数据复制成功: {affected_rows} 行")

            cursor.close()
            connection.close()

            print("\n✓ 完成！\n")

        except Exception as e:
            print(f"\n✗ 错误: {str(e)}\n")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        return

    # 生成表
    if args.command == 'generate':
        try:
            # 处理异常场景
            if hasattr(args, 'invalidScenario') and args.invalidScenario:
                if InvalidCommentTableGenerator is None:
                    print("\n✗ 错误: 无法导入异常场景生成器\n")
                    sys.exit(1)

                print(f"\n{'='*60}")
                print(f"异常场景测试表生成器")
                print(f"{'='*60}")
                print(f"表名: {args.tableName}")
                print(f"异常场景: {args.invalidScenario}")
                print(f"数据行数: {args.rowCount}")
                if args.env:
                    print(f"目标环境: {args.env}")
                print(f"{'='*60}\n")

                create_sql = InvalidCommentTableGenerator.generate_create_table_sql(args.tableName, args.invalidScenario)
                insert_sqls = InvalidCommentTableGenerator.generate_insert_sql(args.tableName, args.rowCount)
                sql_script = create_sql + "\n" + "\n".join(insert_sqls)
            else:
                # 正常场景
                generator = TestTableGenerator(db_type=args.dbType)

                print(f"\n{'='*60}")
                print(f"测试表生成器 (符合 MySQL 建表规范)")
                print(f"{'='*60}")
                print(f"数据库类型: {args.dbType.upper()}")
                print(f"表名: {args.tableName}")
                print(f"数据类型: {args.dataType}")
                print(f"数据行数: {args.rowCount}")
                if args.env:
                    print(f"目标环境: {args.env}")
                print(f"{'='*60}\n")

                sql_script = generator.generate_full_script(
                    table_name=args.tableName,
                    data_type=args.dataType,
                    row_count=args.rowCount,
                    include_drop=args.includeDrop,
                    table_comment=args.tableComment
                )

            # 保存到文件
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(sql_script)
                print(f"✓ SQL 脚本已保存到: {args.output}\n")

            # 执行到数据库
            if args.execute:
                print("正在执行 SQL 到数据库...")
                if hasattr(args, 'invalidScenario') and args.invalidScenario:
                    result = InvalidCommentTableGenerator.execute_sql(args.env, sql_script)
                else:
                    result = generator.execute_sql(
                        sql_script=sql_script,
                        env_name=args.env,
                        host=args.host,
                        port=args.port,
                        database=args.database,
                        username=args.username,
                        password=args.password
                    )

                if result['success']:
                    print(f"✓ {result['message']}")
                    if 'host' in result:
                        print(f"  主机: {result['host']}")
                        print(f"  数据库: {result['database']}")
                else:
                    print(f"✗ 执行失败: {result['error']}")
                    if 'host' in result:
                        print(f"  主机: {result['host']}")
                        print(f"  数据库: {result['database']}")
            else:
                # 只显示 SQL 脚本
                if not args.output:
                    print("生成的 SQL 脚本:")
                    print("-" * 60)
                    print(sql_script)
                    print("-" * 60)

            # 显示连接信息
            if args.showConnection:
                if args.env:
                    env_config = TestTableGenerator.TEST_ENVIRONMENTS[args.env]
                    print("\n预配置环境连接信息:")
                    print("-" * 60)
                    print(f"环境名称: {args.env}")
                    print(f"类型: {env_config['type']}")
                    print(f"主机: {env_config['host']}")
                    print(f"端口: {env_config['port']}")
                    print(f"数据库: {env_config['database']}")
                    print(f"用户名: {env_config['username']}")
                    print(f"密码: {'*' * len(env_config['password'])}")
                    print("-" * 60)
                elif args.host:
                    conn_info = generator.generate_connection_info(
                        host=args.host,
                        port=args.port,
                        database=args.database,
                        username=args.username,
                        password=args.password
                    )
                    print("\nJDBC 连接信息:")
                    print("-" * 60)
                    print(f"Driver: {conn_info['driver']}")
                    print(f"URL: {conn_info['url']}")
                    print(f"Username: {conn_info['username']}")
                    print(f"Password: {'*' * len(conn_info['password']) if conn_info['password'] else '(空)'}")
                    print("-" * 60)

            print("\n✓ 完成！\n")

        except Exception as e:
            print(f"\n✗ 错误: {str(e)}\n")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    main()

