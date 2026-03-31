#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量入仓测试文件生成完整工作流

自动化流程：
1. 创建 N 个测试表（调用 test-table skill）
2. 完善 N 个表的元数据（调用 metadata-complete skill）
3. 生成批量上传文件（调用 template_updater）
"""

import subprocess
import sys
import os
import argparse
import json
from datetime import datetime
from pathlib import Path

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
import config


def log(msg):
    """输出到 stderr"""
    sys.stderr.write(str(msg) + "\n")
    sys.stderr.flush()


def run_command(cmd, description):
    """执行命令并显示结果"""
    log(f"\n{'=' * 70}")
    log(f"正在执行: {description}")
    log(f"{'=' * 70}")
    log(f"命令: {' '.join(cmd)}")
    log("")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        log(f"❌ 执行失败:")
        if e.stdout:
            log(e.stdout)
        return False


def generate_table_names(prefix, count):
    """生成表名列表"""
    timestamp = datetime.now().strftime("%m%d%H%M")
    return [f"{prefix}_{timestamp}_{i+1:02d}" for i in range(count)]


def validate_table_count(count):
    """验证表数量"""
    if count is None or count <= 0:
        return 1
    if count > 3:
        log("⚠️ 建议最多 3 个表便于排查问题，已自动调整为 3 个")
        return 3
    return count


def batch_workflow(
    instance,
    database,
    table_count=1,
    table_prefix="batch_test",
    db_type="mysql",
    extract_method="ins",
    deal_method="merge",
    row_count=10,
    data_type="mixed",
    auto_confirm=False,
    scenario="success"
):
    """
    批量入仓测试文件生成完整工作流
    """
    log("=" * 70)
    log("批量入仓测试文件生成完整工作流")
    log("=" * 70)
    log(f"实例: {instance}")
    log(f"数据库: {database}")
    log(f"表数量: {table_count}")
    log(f"表前缀: {table_prefix}")
    log(f"数据库类型: {db_type}")
    log(f"抽数方式: {extract_method}")
    log(f"处理方式: {deal_method}")
    log(f"场景: {scenario}")
    log("=" * 70)
    log("")

    table_count = validate_table_count(table_count)
    table_names = generate_table_names(table_prefix, table_count)
    
    log(f"将创建以下 {table_count} 个表:")
    for idx, name in enumerate(table_names, 1):
        log(f"  {idx}. {name}")
    log("")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    skill_test_dir = os.path.join(os.path.dirname(current_dir), 'test_excel')
    test_table_script = os.path.join(project_root, "test-table/scripts/index.py")
    metadata_script = os.path.join(project_root, "metadata-complete/scripts/index.py")
    template_updater_script = os.path.join(current_dir, "template_updater.py")

    env_mapping = {
        'cjjcommon': 'cjjcommon',
        'tidb-ares': 'tidb-ares',
        'adb-realtime': 'adb-realtime',
        'bigdata-biz': 'bigdata-biz-dataops'
    }
    env = env_mapping.get(instance, instance)

    created_tables = []

    log("\n" + "=" * 70)
    log("步骤 1: 创建测试表")
    log("=" * 70)

    for idx, table_name in enumerate(table_names, 1):
        log(f"\n[{idx}/{table_count}] 创建表: {table_name}")

        cmd = [
            'python3', test_table_script,
            'generate',
            '--tableName', table_name,
            '--dataType', data_type,
            '--rowCount', str(row_count),
            '--execute',
            '--env', env
        ]

        if run_command(cmd, f"创建表 {table_name}"):
            created_tables.append(table_name)
            log(f"✅ 表 {table_name} 创建成功")
        else:
            log(f"❌ 表 {table_name} 创建失败")
            break

    if len(created_tables) == 0:
        log("\n❌ 没有成功创建任何表，工作流终止")
        output = {
            "status": "error",
            "error": "没有成功创建任何表"
        }
        print("```json\n" + json.dumps(output, ensure_ascii=False, indent=2) + "\n```")
        return False

    log(f"\n✅ 成功创建 {len(created_tables)}/{table_count} 个表")

    if config.is_skip_metadata(scenario):
        log("\n" + "=" * 70)
        log(f"步骤 2: 跳过元数据完善（{scenario} 场景）")
        log("=" * 70)
        completed_tables = created_tables
        log("✅ 跳过元数据完善步骤，表将保持未完善状态")
    else:
        log("\n" + "=" * 70)
        log("步骤 2: 完善元数据")
        log("=" * 70)

        completed_tables = []

        for idx, table_name in enumerate(created_tables, 1):
            log(f"\n[{idx}/{len(created_tables)}] 完善表元数据: {table_name}")

            cmd = [
                'python3', metadata_script,
                '--instance', instance,
                '--database', database,
                '--table', table_name
            ]

            if run_command(cmd, f"完善表 {table_name} 的元数据"):
                completed_tables.append(table_name)
                log(f"✅ 表 {table_name} 元数据完善成功")
            else:
                log(f"❌ 表 {table_name} 元数据完善失败")
                break

    if len(completed_tables) == 0:
        log("\n❌ 没有成功完善任何表的元数据，工作流终止")
        output = {
            "status": "error",
            "error": "没有成功完善任何表的元数据"
        }
        print("```json\n" + json.dumps(output, ensure_ascii=False, indent=2) + "\n```")
        return False

    log(f"\n✅ 成功完善 {len(completed_tables)}/{len(created_tables)} 个表的元数据")

    log("\n" + "=" * 70)
    log("步骤 3: 生成批量上传文件")
    log("=" * 70)

    failed_scenarios = ['failed_F001', 'failed_F002', 'failed_F003', 'failed_F004']

    if scenario in failed_scenarios:
        log(f"使用场景失败模式生成文件: {scenario}")
        generator_script = os.path.join(current_dir, "xlsx_generator.py")

        for table_name in completed_tables:
            cmd = [
                'python3', generator_script,
                database,
                table_name,
                scenario,
                instance
            ]

            if not run_command(cmd, f"生成 {scenario} 场景测试文件"):
                log(f"❌ 表 {table_name} 测试文件生成失败")
                output = {
                    "status": "error",
                    "error": f"表 {table_name} 测试文件生成失败"
                }
                print("```json\n" + json.dumps(output, ensure_ascii=False, indent=2) + "\n```")
                return False
            else:
                log(f"✅ 表 {table_name} 测试文件生成成功")

        output_file = os.path.join(skill_test_dir, f"batch_{scenario}_latest.xlsx")
    else:
        log("使用正常模板模式生成文件")
        cmd = [
            'python3', template_updater_script,
            instance,
            database,
            *completed_tables,
            '--db-type', db_type,
            '--extract-method', extract_method,
            '--deal-method', deal_method
        ]

        if not run_command(cmd, "生成批量上传文件"):
            log(f"\n❌ 批量上传文件生成失败")
            output = {
                "status": "error",
                "error": "批量上传文件生成失败"
            }
            print("```json\n" + json.dumps(output, ensure_ascii=False, indent=2) + "\n```")
            return False

        output_file = os.path.join(skill_test_dir, "batch_test_latest.xlsx")

    absolute_path = os.path.abspath(output_file)
    relative_path = os.path.join(config.get_relative_output_path(), os.path.basename(output_file))

    log(f"\n✅ 批量上传文件生成成功")
    log(f"   包含 {len(completed_tables)} 个表的配置")
    log(f"相对路径: {relative_path}")
    log(f"绝对路径: {absolute_path}")

    log("\n" + "=" * 70)
    log("工作流完成！")
    log("=" * 70)

    output = {
        "status": "success",
        "instances": [instance],
        "databases": [database],
        "tables": completed_tables,
        "file_info": {
            "file_name": os.path.basename(output_file),
            "absolute_path": absolute_path,
            "relative_path": relative_path,
            "table_count": len(completed_tables)
        },
        "config": {
            "db_type": db_type,
            "scenario": scenario,
            "scenario_desc": config.SCENARIOS.get(scenario, scenario),
            "op_type": extract_method,
            "process_type": deal_method
        }
    }

    print("```json\n" + json.dumps(output, ensure_ascii=False, indent=2) + "\n```")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='批量入仓测试文件生成完整工作流',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python batch_workflow.py cjjcommon dataops_shitingjie
  python batch_workflow.py cjjcommon dataops_shitingjie --count 3
  python batch_workflow.py tidb-ares ares --count 2 --db-type tidb
        """
    )

    parser.add_argument('instance', help='实例名（如：cjjcommon）')
    parser.add_argument('database', help='数据库名（如：dataops_shitingjie）')
    parser.add_argument('--count', type=int, default=1, help='表数量（默认 1，最大 3）')
    parser.add_argument('--prefix', default='batch_test', help='表名前缀（默认 batch_test）')
    parser.add_argument('--db-type', default='mysql', help='数据库类型（默认 mysql）')
    parser.add_argument('--extract-method', default='ins', help='抽数方式（默认 ins）')
    parser.add_argument('--deal-method', default='merge', help='处理方式（默认 merge）')
    parser.add_argument('--row-count', type=int, default=10, help='数据行数（默认 10）')
    parser.add_argument('--data-type', default='mixed', help='数据类型（默认 mixed）')
    parser.add_argument('--scenario', default='success', help='场景类型（默认 success）')

    args = parser.parse_args()

    success = batch_workflow(
        instance=args.instance,
        database=args.database,
        table_count=args.count,
        table_prefix=args.prefix,
        db_type=args.db_type,
        extract_method=args.extract_method,
        deal_method=args.deal_method,
        row_count=args.row_count,
        data_type=args.data_type,
        scenario=args.scenario
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
