#!/usr/bin/env python3
"""
生成违反 MySQL 注释规范的测试表 - 用于异常场景测试
违规场景：
1. table_no_chinese - 表注释不包含中文
2. table_short - 表注释少于4个字符
3. field_no_chinese - 字段注释不包含中文
4. field_short - 字段注释少于4个字符
"""

import pymysql
import random
import string
import configparser
import os


class InvalidCommentTableGenerator:
    """生成违规注释的测试表"""

    @staticmethod
    def load_env_config():
        """加载环境配置"""
        config_file = os.path.join(os.path.dirname(__file__), 'db_config.ini')
        config = configparser.ConfigParser()
        config.read(config_file, encoding='utf-8')

        envs = {}
        for section in config.sections():
            envs[section] = {
                'host': config.get(section, 'host'),
                'port': config.getint(section, 'port'),
                'database': config.get(section, 'database'),
                'username': config.get(section, 'username'),
                'password': config.get(section, 'password')
            }
        return envs

    @staticmethod
    def get_invalid_table_comment(scenario):
        """生成违规表注释"""
        if scenario == 'table_no_chinese':
            return 'test table'
        elif scenario == 'table_short':
            return random.choice(['a', 'ab', 'tc'])
        return '正常表注释'

    @staticmethod
    def get_invalid_field_comment(scenario, field_name):
        """生成违规字段注释"""
        if scenario == 'field_no_chinese':
            return f'{field_name}'
        elif scenario == 'field_short':
            return random.choice(['a', 'id', 'no'])
        return f'{field_name}字段'

    @staticmethod
    def generate_create_table_sql(table_name, scenario):
        """生成建表SQL"""
        table_comment = InvalidCommentTableGenerator.get_invalid_table_comment(scenario)

        fields = ["    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键ID'"]

        if scenario in ['field_no_chinese', 'field_short']:
            fields.append(f"    user_name VARCHAR(100) NOT NULL DEFAULT '' COMMENT '{InvalidCommentTableGenerator.get_invalid_field_comment(scenario, 'user_name')}'")
            fields.append(f"    age INT NOT NULL DEFAULT 0 COMMENT '{InvalidCommentTableGenerator.get_invalid_field_comment(scenario, 'age')}'")
            fields.append(f"    email VARCHAR(255) NOT NULL DEFAULT '' COMMENT '{InvalidCommentTableGenerator.get_invalid_field_comment(scenario, 'email')}'")
        else:
            fields.append("    user_name VARCHAR(100) NOT NULL DEFAULT '' COMMENT '用户姓名'")
            fields.append("    age INT NOT NULL DEFAULT 0 COMMENT '年龄'")
            fields.append("    email VARCHAR(255) NOT NULL DEFAULT '' COMMENT '电子邮箱'")

        fields.append("    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'")
        fields.append("    PRIMARY KEY (id)")

        return f"CREATE TABLE IF NOT EXISTS {table_name} (\n" + ",\n".join(fields) + f"\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='{table_comment}';"

    @staticmethod
    def generate_insert_sql(table_name, row_count=2):
        """生成插入数据SQL"""
        sqls = []
        for i in range(row_count):
            user_name = ''.join(random.choices(string.ascii_letters, k=8))
            age = random.randint(18, 60)
            email = f"{user_name.lower()}@test.com"
            sqls.append(f"INSERT INTO {table_name} (user_name, age, email) VALUES ('{user_name}', {age}, '{email}');")
        return sqls

    @staticmethod
    def execute_sql(env_name, sql_script):
        """执行SQL到数据库"""
        envs = InvalidCommentTableGenerator.load_env_config()
        if env_name not in envs:
            return {'success': False, 'error': f'未找到环境: {env_name}'}

        env = envs[env_name]
        try:
            conn = pymysql.connect(host=env['host'], port=env['port'], user=env['username'],
                                 password=env['password'], database=env['database'], charset='utf8mb4')
            cursor = conn.cursor()

            statements = []
            current = []
            for line in sql_script.split('\n'):
                line = line.strip()
                if line.startswith('--') or not line:
                    continue
                current.append(line)
                if line.endswith(';'):
                    statements.append(' '.join(current).rstrip(';'))
                    current = []

            for stmt in statements:
                if stmt.strip():
                    cursor.execute(stmt)

            conn.commit()
            cursor.close()
            conn.close()
            return {'success': True, 'message': '执行成功'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


def main():
    """主函数"""
    scenarios = {
        'table_no_chinese': '表注释不包含中文',
        'table_short': '表注释少于4个字符',
        'field_no_chinese': '字段注释不包含中文',
        'field_short': '字段注释少于4个字符'
    }

    print("\n" + "="*60)
    print("生成违反 MySQL 注释规范的测试表")
    print("="*60)
    print("\n可用的违规场景:")
    for key, desc in scenarios.items():
        print(f"  {key}: {desc}")

    for scenario in scenarios.keys():
        table_name = f"test_invalid_{scenario}"
        print(f"\n{'='*60}")
        print(f"场景: {scenarios[scenario]}")
        print(f"表名: {table_name}")
        print(f"{'='*60}")

        create_sql = InvalidCommentTableGenerator.generate_create_table_sql(table_name, scenario)
        print("\n建表SQL:")
        print(create_sql)

        insert_sqls = InvalidCommentTableGenerator.generate_insert_sql(table_name, 2)
        print("\n插入数据SQL:")
        for sql in insert_sqls:
            print(sql)

        choice = input(f"\n是否执行到 cjjcommon 环境? (y/n): ").strip().lower()
        if choice == 'y':
            full_sql = create_sql + "\n" + "\n".join(insert_sqls)
            result = InvalidCommentTableGenerator.execute_sql('cjjcommon', full_sql)
            print(f"✓ {result['message']}" if result['success'] else f"✗ {result['error']}")

    print("\n" + "="*60)
    print("完成!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
