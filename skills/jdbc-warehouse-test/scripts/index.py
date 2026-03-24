#!/usr/bin/env python3
"""
JDBC Warehouse Test Skill - 入口脚本
支持命令行直接调用和 Claude Code skill 调用
"""
import sys
import os
import argparse
import subprocess

from xlsx_generator import XlsxGenerator
import config


def call_test_table(source_table, env):
    """
    调用 test-table skill 创建表

    Args:
        source_table: 源表名
        env: 环境名

    Returns:
        str: 新表名，失败返回 None
    """
    try:
        print(f"\n[test-table] 正在克隆表 {source_table}...")

        test_table_script = os.path.join(
            os.path.dirname(__file__),
            "../../test-table/scripts/index.py"
        )

        result = subprocess.run(
            ["python", test_table_script, "copy-table",
             "--sourceTable", source_table,
             "--env", env],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            # 从输出中提取新表名
            for line in result.stdout.split('\n'):
                if '✓ 自动生成目标表名:' in line:
                    new_table = line.split(':')[-1].strip()
                    print(f"[test-table] ✓ 表克隆成功: {new_table}")
                    return new_table

            print("[test-table] ⚠️  未能获取新表名")
            return None
        else:
            print(f"[test-table] ✗ 克隆失败: {result.stderr}")
            return None

    except Exception as e:
        print(f"[test-table] ✗ 调用失败: {str(e)}")
        return None


def call_metadata_complete(database, table):
    """
    调用 metadata-complete skill 完善元数据

    Args:
        database: 数据库名
        table: 表名

    Returns:
        bool: 是否成功
    """
    try:
        print(f"\n[metadata-complete] 正在完善元数据...")

        metadata_script = os.path.join(
            os.path.dirname(__file__),
            "../../metadata-complete/scripts/index.py"
        )

        result = subprocess.run(
            ["python", metadata_script,
             "--database", database,
             "--table", table],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("[metadata-complete] ✓ 元数据完善成功")
            return True
        else:
            print(f"[metadata-complete] ⚠️  元数据完善失败，但继续生成测试文件")
            return False

    except Exception as e:
        print(f"[metadata-complete] ✗ 调用失败: {str(e)}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='JDBC 入仓批量测试文件生成器'
    )

    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # generate 命令
    gen_parser = subparsers.add_parser('generate', help='生成测试文件')

    gen_parser.add_argument(
        '--database',
        help='数据库名称（如：stjtestadb）'
    )

    gen_parser.add_argument(
        '--table',
        help='表名（如：adb_json_batch_01）'
    )

    gen_parser.add_argument(
        '--scenario',
        default='success',
        choices=list(config.SCENARIOS.keys()),
        help='测试场景（默认：success）'
    )

    gen_parser.add_argument(
        '--env',
        help='环境名称（如：adb-realtime）'
    )

    gen_parser.add_argument(
        '--dbType',
        choices=['mysql', 'tidb', 'adb'],
        help='数据源类型（可选，自动推断）'
    )

    gen_parser.add_argument(
        '--output',
        help='输出路径（可选）'
    )

    # 集成模式参数
    gen_parser.add_argument(
        '--createTable',
        action='store_true',
        help='是否先创建表（需要同时提供 --sourceTable 和 --env）'
    )

    gen_parser.add_argument(
        '--sourceTable',
        help='源表名（仅在 --createTable 模式需要）'
    )

    gen_parser.add_argument(
        '--completeMetadata',
        action='store_true',
        default=True,
        help='是否完善元数据（默认：true）'
    )

    args = parser.parse_args()

    if args.command != 'generate':
        parser.print_help()
        return 1

    # ========== 执行流程 ==========

    database = args.database
    table = args.table

    # 集成模式：先创建表
    if args.createTable:
        if not args.sourceTable or not args.env:
            print("✗ 错误: --createTable 模式需要提供 --sourceTable 和 --env")
            return 1

        new_table = call_test_table(args.sourceTable, args.env)
        if not new_table:
            print("✗ 创建表失败")
            return 1

        table = new_table

        # 从环境名推断数据库（需要查询 test-table 的配置）
        # 简化处理：使用命令行提供的 database 或从 env 推断
        if not database:
            # 根据 env 推断 database
            env_db_mapping = {
                'adb-realtime': 'stjtestadb',
                'tidb-ares': 'ares',
                'cjjcommon': 'dataops_shitingjie'
            }
            database = env_db_mapping.get(args.env)
            if not database:
                print(f"✗ 错误: 无法从环境 {args.env} 推断数据库名，请使用 --database 指定")
                return 1

    # 验证必需参数
    if not database or not table:
        print("✗ 错���: 必须提供 --database 和 --table")
        return 1

    # 完善元数据
    if args.completeMetadata and args.scenario != 'failed_F004':
        call_metadata_complete(database, table)

    # 生成测试文件
    generator = XlsxGenerator()
    result = generator.generate(
        database=database,
        table=table,
        scenario=args.scenario,
        env=args.env,
        output_path=args.output
    )

    if result['success']:
        return 0
    else:
        return 1


if __name__ == '__main__':
    sys.exit(main())
