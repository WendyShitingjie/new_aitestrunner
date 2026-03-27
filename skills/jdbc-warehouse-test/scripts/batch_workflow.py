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
from datetime import datetime
from pathlib import Path

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
import config


def run_command(cmd, description):
    """执行命令并显示结果"""
    print(f"\n{'=' * 70}")
    print(f"正在执行: {description}")
    print(f"{'=' * 70}")
    print(f"命令: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print("警告:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 执行失败:")
        print(e.stdout)
        print(e.stderr)
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
        print("⚠️ 建议最多 3 个表便于排查问题，已自动调整为 3 个")
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

    Args:
        instance: 实例名（如：cjjcommon）
        database: 数据库名（如：dataops_shitingjie）
        table_count: 表数量（1-3，默认 1）
        table_prefix: 表名前缀（默认 batch_test）
        db_type: 数据库类型（mysql/tidb/adb）
        extract_method: 抽数方式（all/ins）
        deal_method: 处理方式（all/ins/merge）
        row_count: 每个表的数据行数（默认 10）
        data_type: 数据类型（string/number/date/boolean/mixed）
    """

    print("=" * 70)
    print("批量入仓测试文件生成完整工作流")
    print("=" * 70)
    print(f"实例: {instance}")
    print(f"数据库: {database}")
    print(f"表数量: {table_count}")
    print(f"表前缀: {table_prefix}")
    print(f"数据库类型: {db_type}")
    print(f"抽数方式: {extract_method}")
    print(f"处理方式: {deal_method}")
    print("=" * 70)
    print()

    # 验证表数量
    table_count = validate_table_count(table_count)

    # 生成表名列表
    table_names = generate_table_names(table_prefix, table_count)
    print(f"将创建以下 {table_count} 个表:")
    for idx, name in enumerate(table_names, 1):
        print(f"  {idx}. {name}")
    print()

    # 确认继续
    if not auto_confirm:
        confirm = input("是否继续？(y/n): ")
        if confirm.lower() != 'y':
            print("已取消")
            return False
    else:
        print("自动确认模式，继续执行...")

    # 获取脚本路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))  # 指向 skills 目录
    skill_test_dir = os.path.join(os.path.dirname(current_dir), 'test_excel')
    test_table_script = os.path.join(project_root, "test-table/scripts/index.py")
    metadata_script = os.path.join(project_root, "metadata-complete/scripts/index.py")
    template_updater_script = os.path.join(current_dir, "template_updater.py")

    # 根据实例名映射环境名
    env_mapping = {
        'cjjcommon': 'cjjcommon',
        'tidb-ares': 'tidb-ares',
        'adb-realtime': 'adb-realtime',
        'bigdata-biz': 'bigdata-biz-dataops'
    }
    env = env_mapping.get(instance, instance)

    created_tables = []

    # Step 1: 创建测试表
    print("\n" + "=" * 70)
    print("步骤 1: 创建测试表")
    print("=" * 70)

    for idx, table_name in enumerate(table_names, 1):
        print(f"\n[{idx}/{table_count}] 创建表: {table_name}")

        cmd = [
            'python3', test_table_script,
            'generate',
            '--tableName', table_name,
            '--dataType', data_type,
            '--rowCount', str(row_count),
            '--execute',
            '--env', env
        ]

        if run_command(cmd, f"创建��� {table_name}"):
            created_tables.append(table_name)
            print(f"✅ 表 {table_name} 创建成功")
        else:
            print(f"❌ 表 {table_name} 创建失败")
            print("是否继续创建剩余表？(y/n): ", end='')
            if input().lower() != 'y':
                break

    if len(created_tables) == 0:
        print("\n❌ 没有成功创建任何表，工作流终止")
        return False

    print(f"\n✅ 成功创建 {len(created_tables)}/{table_count} 个表")

    # Step 2: 完善元数据（根据场景配置决定）
    if config.is_skip_metadata(scenario):
        print("\n" + "=" * 70)
        print(f"步骤 2: 跳过元数据完善（{scenario} 场景）")
        print("=" * 70)
        completed_tables = created_tables
        print("✅ 跳过元数据完善步骤，表将保持未完善状态")
    else:
        print("\n" + "=" * 70)
        print("步骤 2: 完善元数据")
        print("=" * 70)

        completed_tables = []

        for idx, table_name in enumerate(created_tables, 1):
            print(f"\n[{idx}/{len(created_tables)}] 完善表元数据: {table_name}")

            cmd = [
                'python3', metadata_script,
                '--instance', instance,
                '--database', database,
                '--table', table_name
            ]

            if run_command(cmd, f"完善表 {table_name} 的元数据"):
                completed_tables.append(table_name)
                print(f"✅ 表 {table_name} 元数据完善成功")
            else:
                print(f"❌ 表 {table_name} 元数据完善失败")
                print("是否继续处理剩余表？(y/n): ", end='')
                if input().lower() != 'y':
                    break

    if len(completed_tables) == 0:
        print("\n❌ 没有成功完善任何表的元数据，工作流终止")
        return False

    print(f"\n✅ 成功完善 {len(completed_tables)}/{len(created_tables)} 个表的元数据")

    # Step 3: 生成批量上传文件
    print("\n" + "=" * 70)
    print("步骤 3: 生成批量上传文件")
    print("=" * 70)

    # 根据场景选择生成器
    # success: 使用 template_updater.py（正常模板）
    # failed_F001/F002/F003/F004: 使用 xlsx_generator.py（场景失败数据）
    failed_scenarios = ['failed_F001', 'failed_F002', 'failed_F003', 'failed_F004']

    if scenario in failed_scenarios:
        print(f"使用场景失败模式生成文件: {scenario}")
        generator_script = os.path.join(current_dir, "xlsx_generator.py")

        for table_name in completed_tables:
            cmd = [
                'python3', generator_script,
                database,
                table_name,
                scenario,
                instance
            ]

            if run_command(cmd, f"生成 {scenario} 场景测试文件"):
                print(f"✅ 表 {table_name} 测试文件生成成功")
            else:
                print(f"❌ 表 {table_name} 测试文件生成失败")
                return False

        output_file = os.path.join(skill_test_dir, f"batch_{scenario}_latest.xlsx")
    else:
        print("使用正常模板模式生成文件")
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
            print(f"\n❌ 批量上传文件生成失败")
            return False

        output_file = os.path.join(skill_test_dir, "batch_test_latest.xlsx")

    print(f"\n✅ 批量上传文件生成成功")
    print(f"   包含 {len(completed_tables)} 个表的配置")
    # 同时输出相对路径和绝对路径，供框架灵活选择
    relative_path = os.path.join(config.get_relative_output_path(), os.path.basename(output_file))
    print(f"相对路径: {relative_path}")
    print(f"绝对路径: {os.path.abspath(output_file)}")

    print("\n" + "=" * 70)
    print("工作流完成！")
    print("=" * 70)
    print("\n后续步骤:")
    print("1. 上传测试:")
    print("   python batch_upload_validate.py \\")
    print('     "test_excel/batch_test_latest.xlsx"')
    print()
    print("2. 查询结果:")
    print("   python batch_query_result.py <taskId>")
    print()
    print("3. 提交任务:")
    print("   python batch_submit_task.py <taskId>")
    print()

    return True


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='批量入仓测试文件生成完整工作流',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法（默认 1 个表）
  python batch_workflow.py cjjcommon dataops_shitingjie

  # 指定 3 个表
  python batch_workflow.py cjjcommon dataops_shitingjie --count 3

  # TiDB 环境 2 个表
  python batch_workflow.py tidb-ares ares --count 2 --db-type tidb

  # 自定义表名前缀和数据行数
  python batch_workflow.py cjjcommon dataops_shitingjie --count 3 \\
    --prefix my_test --row-count 20
        """
    )

    parser.add_argument('instance', help='实例名（如：cjjcommon）')
    parser.add_argument('database', help='数据库名（如：dataops_shitingjie）')
    parser.add_argument('--count', type=int, default=1,
                        help='表数量（1-3，默认 1）')
    parser.add_argument('--prefix', default='batch_test',
                        help='表名前缀（默认 batch_test）')
    parser.add_argument('--db-type', default='mysql',
                        choices=['mysql', 'tidb', 'adb'],
                        help='数据库类型（默认 mysql）')
    parser.add_argument('--extract-method', default='ins',
                        choices=['all', 'ins'],
                        help='抽数方式（��认 ins）')
    parser.add_argument('--deal-method', default='merge',
                        choices=['all', 'ins', 'merge'],
                        help='处理方式（默认 merge）')
    parser.add_argument('--row-count', type=int, default=10,
                        help='每个表的数据行数（默认 10）')
    parser.add_argument('--data-type', default='mixed',
                        choices=['string', 'number', 'date', 'boolean', 'mixed'],
                        help='数据类型（默认 mixed）')
    parser.add_argument('--yes', '-y', action='store_true',
                        help='自动确认，跳过交互式提示')
    parser.add_argument('--scenario', default='success',
                        help='场景类型：success, failed_F001, failed_F002, failed_F003, failed_F004')

    args = parser.parse_args()

    # 验证抽数方式和处理方式的组合
    valid_combinations = [
        ('all', 'all'),
        ('ins', 'merge'),
        ('ins', 'ins'),
    ]

    if (args.extract_method, args.deal_method) not in valid_combinations:
        print("❌ 错误：抽数方式和处理方式组合不合法")
        print()
        print("合法组合：")
        print("  - all + all   (全量覆盖)")
        print("  - ins + merge (增量合并)")
        print("  - ins + ins   (增量分区)")
        print()
        sys.exit(1)

    try:
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
            auto_confirm=args.yes,
            scenario=args.scenario
        )
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
