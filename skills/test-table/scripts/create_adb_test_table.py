#!/usr/bin/env python3
"""
在 stjtestadb 库创建测试表
参考 adb_json_batch_01 的结构创建新表并插入测试数据
"""

import pymysql
import json
from datetime import datetime
import random
import string

# ADB 数据库配置
DB_CONFIG = {
    'host': 'sitadbrealtimedw.adb.ali-bj-sit01.shuheo.net',
    'port': 3306,
    'user': 'shuhe_dev_448679',
    'password': 'shuhe_dev_448679c_251874',
    'database': 'stjtestadb',
    'charset': 'utf8mb4'
}


def get_dynamic_table_name():
    """生成带时间戳的表名，例如：adb_json_batch_test_0227_153045"""
    timestamp = datetime.now().strftime('%m%d_%H%M%S')
    return f'adb_json_batch_test_{timestamp}'


# 新表名
NEW_TABLE_NAME = 'adb_json_batch_test_0227'


# 建表 DDL（基于 adb_json_batch_01 的结构）
def get_create_table_ddl(table_name):
    """根据动态表名生成建表 DDL"""
    return f"""
    CREATE TABLE `{table_name}` (
     `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'idid中文',
     `email` varchar(20) NOT NULL COMMENT '电子邮箱L3',
     `content` json NOT NULL COMMENT 'json字段',
     `password` varchar(255) NOT NULL COMMENT '账号密码',
     `created_by` varchar(20) NOT NULL DEFAULT '' COMMENT '创建人',
     `updated_by` varchar(20) NOT NULL DEFAULT '' COMMENT '更新人',
     `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
     `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',
     `GIBGI` varchar(20) NOT NULL DEFAULT '' COMMENT '测试字段',
     primary key (`id`)
    ) DISTRIBUTE BY HASH(`id`) INDEX_ALL='Y' STORAGE_POLICY='HOT' ENGINE='XUANWU' 
    TABLE_PROPERTIES='{{"format":"columnstore"}}' COMMENT='动态生成测试表'
    """


def generate_random_email():
    """生成随机邮箱"""
    domains = ['test.com', 'demo.com', 'example.com']
    username = ''.join(random.choices(string.ascii_lowercase, k=6))
    return f"{username}@{random.choice(domains)}"


def generate_random_password():
    """生成随机密码"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=12))


def generate_json_content():
    """生成随机 JSON 内容"""
    return json.dumps({
        'name': f'测试用户{random.randint(1, 100)}',
        'age': random.randint(18, 60),
        'city': random.choice(['北京', '上海', '深圳', '杭州']),
        'score': round(random.uniform(60, 100), 2)
    }, ensure_ascii=False)


def create_table_and_insert_data():
    """创建表并插入测试数据"""
    connection = None
    NEW_TABLE_NAME = get_dynamic_table_name()
    CREATE_TABLE_DDL = get_create_table_ddl(NEW_TABLE_NAME)
    try:
        # 连接数据库
        print("=" * 80)
        print("ADB 测试表创建工具")
        print("=" * 80)
        print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"数据库: {DB_CONFIG['database']}")
        print(f"新表名: {NEW_TABLE_NAME}")
        print("=" * 80)
        print()

        print(f"正在连接 ADB 数据库: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # 1. 检查表是否已存在（虽然带时间戳重名概率极低，但作为规范保留）
        cursor.execute(f"SHOW TABLES LIKE '{NEW_TABLE_NAME}'")
        if cursor.fetchone():
            print(f"⚠️  表 {NEW_TABLE_NAME} 意外存在，将先删除")
            cursor.execute(f"DROP TABLE {NEW_TABLE_NAME}")
            connection.commit()
            print(f"✓ 已删除旧表")

        # 2. 创建新表
        print(f"\n正在创建表 {NEW_TABLE_NAME}...")
        cursor.execute(CREATE_TABLE_DDL)
        connection.commit()
        print(f"✅ 表创建成功")

        # 3. 插入5条测试数据
        print(f"\n正在插入测试数据...")
        insert_sql = f"""
        INSERT INTO `{NEW_TABLE_NAME}`
        (`email`, `content`, `password`, `created_by`, `updated_by`, `GIBGI`)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        test_data = []
        for i in range(5):
            test_data.append((
                generate_random_email(),
                generate_json_content(),
                generate_random_password(),
                f'user_{i + 1}',
                f'user_{i + 1}',
                f'test_{i + 1}'
            ))

        cursor.executemany(insert_sql, test_data)
        connection.commit()
        print(f"✅ 成功插入 {cursor.rowcount} 条数据")

        # 4. 查询验证
        print(f"\n正在验证数据...")
        cursor.execute(f"SELECT COUNT(*) FROM {NEW_TABLE_NAME}")
        count = cursor.fetchone()[0]
        print(f"✓ 表中共有 {count} 条数据")

        # 5. 显示表结构
        print(f"\n表 {NEW_TABLE_NAME} 结构信息:")
        cursor.execute(f"DESCRIBE {NEW_TABLE_NAME}")
        columns = cursor.fetchall()
        print(f"{'字段名':<20} {'类型':<20} {'是否为空':<10} {'键':<10} {'默认值':<20}")
        print("-" * 90)
        for col in columns:
            field, type_, null, key, default, extra = col
            print(f"{field:<20} {type_:<20} {null:<10} {key:<10} {str(default):<20}")

        # 6. 显示部分数据
        print(f"\n表 {NEW_TABLE_NAME} 数据预览（前3条）:")
        cursor.execute(f"SELECT id, email, content, created_by FROM {NEW_TABLE_NAME} LIMIT 3")
        rows = cursor.fetchall()
        print(f"{'ID':<10} {'Email':<25} {'JSON内容':<50} {'创建人':<15}")
        print("-" * 100)
        for row in rows:
            id_, email, content, created_by = row
            content_preview = content[:47] + '...' if len(content) > 50 else content
            print(f"{id_:<10} {email:<25} {content_preview:<50} {created_by:<15}")

        print("\n" + "=" * 80)
        print("✅ 表创建和数据插入完成")
        print(f"表名: {NEW_TABLE_NAME}")
        print(f"数据库: {DB_CONFIG['database']}")
        print(f"数据行数: {count}")
        print("=" * 80)

        return True

    except pymysql.Error as e:
        print(f"\n❌ 数据库错误: {e}")
        if connection:
            connection.rollback()
        return False
    except Exception as e:
        print(f"\n❌ 执行错误: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if connection:
            cursor.close()
            connection.close()
            print(f"\n数据库连接已关闭")


if __name__ == "__main__":
    create_table_and_insert_data()
