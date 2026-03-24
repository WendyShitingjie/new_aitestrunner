#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 cjjcommon 数据库复制表结构
根据现有表的 DDL 创建新的测试表
"""

import pymysql
import sys

# 数据库连接配置
config = {
    'host': 'cjjcommon.db.ali-bj-sit01.shuheo.net',
    'port': 3306,
    'user': 'sit_shitingjie',
    'password': 'sit_user_115e27b_932c93',
    'database': 'dataops_shitingjie',
    'charset': 'utf8mb4'
}

def get_table_ddl(connection, table_name):
    """获取表的 DDL"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"SHOW CREATE TABLE `{table_name}`")
            result = cursor.fetchone()
            if result:
                return result[1]
            else:
                print(f"❌ �� {table_name} 不存在")
                return None
    except Exception as e:
        print(f"❌ 获取表 DDL 失败: {e}")
        return None

def create_new_table(connection, old_table_name, new_table_name):
    """根据旧表 DDL 创建新表"""
    try:
        # 获取旧表的 DDL
        ddl = get_table_ddl(connection, old_table_name)
        if not ddl:
            return False

        print(f"\n📋 原表 {old_table_name} 的 DDL:")
        print("=" * 80)
        print(ddl)
        print("=" * 80)

        # 替换表名
        new_ddl = ddl.replace(f'CREATE TABLE `{old_table_name}`',
                             f'CREATE TABLE `{new_table_name}`', 1)

        print(f"\n📋 新表 {new_table_name} 的 DDL:")
        print("=" * 80)
        print(new_ddl)
        print("=" * 80)

        # 执行创建新表
        with connection.cursor() as cursor:
            cursor.execute(new_ddl)
            connection.commit()
            print(f"\n✅ 新表 {new_table_name} 创建成功！")
            return True

    except pymysql.err.OperationalError as e:
        if e.args[0] == 1050:  # 表已存在
            print(f"\n⚠️  表 {new_table_name} 已存在")
            return False
        else:
            print(f"❌ 创建表失败: {e}")
            return False
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        return False

def main():
    old_table_name = 'test_amart'
    new_table_name = 'test_meta_complete'

    print(f"🔄 开始复制表结构...")
    print(f"源表: {old_table_name}")
    print(f"目标表: {new_table_name}")
    print(f"数据库: {config['database']}")
    print(f"主机: {config['host']}\n")

    try:
        # 连接数据库
        connection = pymysql.connect(**config)
        print("✅ 数据库连接成功\n")

        # 创建新表
        success = create_new_table(connection, old_table_name, new_table_name)

        if success:
            # 查询新表结构
            with connection.cursor() as cursor:
                cursor.execute(f"DESC `{new_table_name}`")
                columns = cursor.fetchall()
                print(f"\n📊 新表 {new_table_name} 的字段信息:")
                print("-" * 80)
                for col in columns:
                    print(f"  {col[0]:20s} {col[1]:30s} {col[2]:10s} {col[3]:10s}")
                print("-" * 80)

        connection.close()

    except Exception as e:
        print(f"❌ 操作失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
