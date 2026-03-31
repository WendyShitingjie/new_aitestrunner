#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JDBC Warehouse Test Skill - 入口脚本
支持命令行直接调用和 Claude Code skill 调用
"""
import sys
import os
import json
import argparse
import subprocess

from xlsx_generator import XlsxGenerator
import config
import template_updater


def log(msg):
    """输出到 stderr"""
    sys.stderr.write(str(msg) + "\n")
    sys.stderr.flush()


def call_test_table(source_table, env):
    """
    调用 test-table skill 克隆表

    Args:
        source_table: 源表名
        env: 环境名

    Returns:
        str: 新表名，失败返回 None
    """
    try:
        log(f"\n[test-table] 正在克隆表 {source_table}...")

        test_table_script = os.path.join(
            os.path.dirname(__file__),
            "../../test-table/scripts/index.py"
        )

        result = subprocess.run(
            ["python3", test_table_script, "copy-table",
             "--sourceTable", source_table,
             "--env", env],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )

        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if '✓ 自动生成目标表名:' in line:
                    new_table = line.split(':')[-1].strip()
                    log(f"[test-table] ✓ 表克隆成功: {new_table}")
                    return new_table

            log("[test-table] ⚠️  未能获取新表名")
            return None
        else:
            log(f"[test-table] ✗ 克隆失败: {result.stderr}")
            return None

    except Exception as e:
        log(f"[test-table] ✗ 调用失败: {str(e)}")
        return None


def call_test_table_generate(env, db_type='adb', table_prefix='test_auto'):
    """
    调用 test-table skill 生成默认结构的新表

    Args:
        env: 环境名
        db_type: 数据库类型
        table_prefix: 表名前缀

    Returns:
        str: 新表名，失败返回 None
    """
    try:
        import time
        timestamp = int(time.time())
        table_name = f"{table_prefix}_{timestamp}"

        log(f"\n[test-table] 正在生成默认结构表 {table_name}...")

        test_table_script = os.path.join(
            os.path.dirname(__file__),
            "../../test-table/scripts/index.py"
        )

        result = subprocess.run(
            ["python3", test_table_script, "generate",
             "--tableName", table_name,
             "--dataType", "mixed",
             "--env", env,
             "--dbType", db_type,
             "--execute"],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )

        if result.returncode == 0:
            log(f"[test-table] ✓ 表生成成功: {table_name}")
            return table_name
        else:
            log(f"[test-table] ✗ 生成失败: {result.stderr}")
            return None

    except Exception as e:
        log(f"[test-table] ✗ 调用失败: {str(e)}")
        return None


def infer_env_from_database(database: str) -> str:
    """
    从数据库名推断环境名

    Args:
        database: 数据库名

    Returns:
        str: 环境名，未找到返回 None
    """
    db_to_env = {
        'dataops_shitingjie': 'cjjcommon',
        'stjtestadb': 'adb-realtime',
        'ares': 'tidb-ares',
        'datahub': 'cjjloan',
        'dataops': 'bigdata-biz-dataops',
    }
    return db_to_env.get(database)


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
        log(f"\n[metadata-complete] 正在完善元数据...")

        metadata_script = os.path.join(
            os.path.dirname(__file__),
            "../../metadata-complete/scripts/index.py"
        )

        result = subprocess.run(
            ["python3", metadata_script,
             "--database", database,
             "--table", table],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            log("[metadata-complete] ✓ 元数据完善成功")
            return True
        else:
            log(f"[metadata-complete] ⚠️  元数据完善失败，但继续生成测试文件")
            return False

    except Exception as e:
        log(f"[metadata-complete] ✗ 调用失败: {str(e)}")
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
        '--tables',
        nargs='+',
        help='表名列表（如：adb_json_batch_01 adb_json_batch_02）'
    )

    gen_parser.add_argument(
        '--table',
        help='表名（单表模式，如：adb_json_batch_01）'
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

    gen_parser.add_argument(
        '--tablePrefix',
        default='test_auto',
        help='自动生成表时的表名前缀（默认：test_auto）'
    )

    args = parser.parse_args()

    if args.command != 'generate':
        parser.print_help()
        return 1

    # ========== 执行流程 ==========

    database = args.database

    # 检查场景配置是否需要跳过元数据完善
    scenario_skip_metadata = False
    scenario_config_path = os.path.join(os.path.dirname(__file__), 'scenario_config.json')
    if os.path.exists(scenario_config_path):
        with open(scenario_config_path, 'r') as f:
            scenario_data = json.load(f).get('scenarios', {}).get(args.scenario or 'success', {})
            scenario_skip_metadata = scenario_data.get('skip_metadata', False)

    # 多表模式：使用 template_updater
    if args.tables:
        tables = args.tables
        
        # 如果提供了 --tablePrefix，自动生成新表
        if args.tablePrefix:
            if not args.env:
                log("✗ 错误: 自动生成表需要提供 --env")
                return 1
            
            prefix = args.tablePrefix
            db_type = args.dbType or 'mysql'
            table_count = len(tables)
            
            tables = []
            for i in range(1, table_count + 1):
                table_name = f"{prefix}_{i}"
                log(f"\n[自动创建] 正在生成表 {table_name}...")
                new_table = call_test_table_generate(args.env, db_type, table_name)
                if new_table:
                    tables.append(new_table)
                    if not scenario_skip_metadata:
                        call_metadata_complete(database, new_table)
                else:
                    log(f"✗ 表 {table_name} 创建失败")
            
            if len(tables) == 0:
                log("✗ 没有成功创建任何表")
                return 1
        
        if not database:
            log("✗ 错误: 多表模式必须提供 --database")
            return 1

        log(f"\n[批量模式] 正在为 {len(tables)} 个表生成测试文件...")

        # 完善元数据
        if args.completeMetadata and not scenario_skip_metadata:
            for t in tables:
                call_metadata_complete(database, t)

        # 使用 template_updater 生成多表测试文件
        try:
            output_file = template_updater.update_template_batch(
                instance=args.env or infer_env_from_database(database),
                database=database,
                tables=tables,
                db_type=args.dbType or 'mysql',
                extract_method='ins',
                deal_method='merge',
                scenario=args.scenario or 'success'
            )

            output = {
                "status": "success",
                "instances": [args.env or infer_env_from_database(database)],
                "databases": [database],
                "tables": tables,
                "file_info": {
                    "file_name": os.path.basename(output_file),
                    "absolute_path": os.path.abspath(output_file),
                    "relative_path": output_file.replace(os.getcwd() + '/', ''),
                    "table_count": len(tables)
                },
                "config": {
                    "db_type": args.dbType or 'mysql',
                    "scenario": args.scenario,
                    "scenario_desc": config.SCENARIOS.get(args.scenario, ''),
                    "op_type": "ins",
                    "process_type": "merge"
                }
            }

            print("```json\n" + json.dumps(output, ensure_ascii=False, indent=2) + "\n```")
            return 0

        except Exception as e:
            output = {
                "status": "error",
                "error_code": "MULTI_TABLE_FAILED",
                "message": str(e),
                "received_params": {
                    "database": database,
                    "tables": tables,
                    "scenario": args.scenario
                }
            }
            print("```json\n" + json.dumps(output, ensure_ascii=False, indent=2) + "\n```")
            return 1

    table = args.table

    # 集成模式：先创建表
    if args.createTable:
        if not args.sourceTable or not args.env:
            log("✗ 错误: --createTable 模式需要提供 --sourceTable 和 --env")
            return 1

        new_table = call_test_table(args.sourceTable, args.env)
        if not new_table:
            log("✗ 创建表失败")
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
                log(f"✗ 错误: 无法从环境 {args.env} 推断数据库名，请使用 --database 指定")
                return 1

    # 验证必需参数
    if not database or not table:
        # 如果没有提供 table 但提供了 env 或 database，自动生成一个默认结构的表
        if not table and (args.env or args.database):
            # 双向推断：env ↔ database
            if args.env and not args.database:
                env_db_mapping = {
                    'adb-realtime': 'stjtestadb',
                    'tidb-ares': 'ares',
                    'cjjcommon': 'dataops_shitingjie'
                }
                database = args.database or env_db_mapping.get(args.env)
            elif args.database and not args.env:
                args.env = infer_env_from_database(args.database)

            if not args.env:
                log("✗ 错误: 无法从 database 推断环境，请使用 --env 指定")
                return 1

            db_type = args.dbType or 'adb'
            new_table = call_test_table_generate(args.env, db_type, args.tablePrefix)
            if not new_table:
                log("✗ 自动生成表失败")
                return 1
            table = new_table
            database = args.database
        else:
            log("✗ 错误: 必须提供 --database 和 --table，或提供 --env 自动生成")
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
        table_info = result.get('table_info', {})
        time_fields = result.get('time_fields', {})

        extract, process = config.get_extract_process(args.scenario)

        output = {
            "status": "success",
            "instances": [table_info.get('instance', args.env or '')],
            "databases": [table_info.get('database', database)],
            "tables": [table],
            "file_info": {
                "file_name": result.get('filename', ''),
                "absolute_path": result.get('absolute_path', ''),
                "relative_path": result.get('relative_path', ''),
                "column_count": len(table_info.get('columns', [])),
                "primary_key": table_info.get('primary_key', '')
            },
            "time_fields": {
                "created_field": time_fields.get('created_field', ''),
                "updated_field": time_fields.get('updated_field', '')
            },
            "config": {
                "db_type": table_info.get('db_type', ''),
                "scenario": args.scenario,
                "scenario_desc": config.SCENARIOS.get(args.scenario, ''),
                "op_type": extract or '',
                "process_type": process or ''
            }
        }
    else:
        output = {
            "status": "error",
            "error_code": "GENERATE_FAILED",
            "message": result.get('message', '生成失败'),
            "received_params": {
                "database": database,
                "table": table,
                "scenario": args.scenario,
                "env": args.env
            }
        }

    print("```json\n" + json.dumps(output, ensure_ascii=False, indent=2) + "\n```")

    return 0 if result['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
