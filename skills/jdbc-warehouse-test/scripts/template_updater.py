#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量入仓测试文件模板更新器
从固定模板文件读取，更新关键字段后生成最新测试文件
"""

import pandas as pd
import os
import sys
import json
from datetime import datetime


def log(msg):
    """输出到 stderr"""
    sys.stderr.write(str(msg) + "\n")
    sys.stderr.flush()


# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)

# 模板文件路径（相对于 skill 目录）
TEMPLATE_FILE = os.path.join(SKILL_DIR, 'templates', 'batch_success_template.xlsx')
OUTPUT_FILE = os.path.join(SKILL_DIR, 'test_excel', 'batch_test_latest.xlsx')


def update_template_batch(
    instance,
    database,
    tables,
    db_type="mysql",
    extract_method="ins",
    deal_method="merge",
    scenario="success"
):
    """
    批量更新模板文件生成最新测试文件（支持多个表）

    Args:
        instance: 实例名（如：cjjcommon）
        database: 数据库名（如：dataops_shitingjie）
        tables: 表名列表（如：['test_table_001', 'test_table_002']）
        db_type: 数据库类型（mysql/tidb/adb），默认 mysql
        extract_method: 抽数方式（all=全量，ins=增量），默认 ins
        deal_method: 处理方式（all=覆盖，ins=分区，merge=合并），默认 merge

    Returns:
        str: 生成的文件路径
    """
    # 参数验证
    if not isinstance(tables, list):
        tables = [tables]

    if len(tables) == 0:
        raise ValueError("表名列表不能为空")

    if len(tables) > 3:
        log(f"⚠️ 建议最多 3 个表，已自动调整为 3 个表")
        tables = tables[:3]

    log("=" * 70)
    log("批量入仓测试文件模板更新器（批量模式）")
    log("=" * 70)
    log(f"模板文件: {os.path.basename(TEMPLATE_FILE)}")
    log(f"输出文件: {os.path.basename(OUTPUT_FILE)}")
    log(f"表数量: {len(tables)}")
    log("=" * 70)
    log("")

    # 检查模板文件是否存在
    if not os.path.exists(TEMPLATE_FILE):
        raise FileNotFoundError(f"模板文件不存在: {TEMPLATE_FILE}")

    # 读取模板文件
    log("正在读取模板文件...")
    df = pd.read_excel(TEMPLATE_FILE, engine='openpyxl')

    log(f"✓ 模板文件读取成功（{len(df)} 行 × {len(df.columns)} 列）")
    log("")

    # 获取模板行（第一行）
    template_row = df.iloc[0].copy()

    # 加载场景配置
    import json
    scenario_config = {}
    config_path = os.path.join(SKILL_DIR, 'scripts', 'scenario_config.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            scenario_config = json.load(f).get('scenarios', {}).get(scenario, {})

    # 如果场景配置中有 extract 和 process，覆盖默认值
    if scenario_config.get('extract'):
        extract_method = scenario_config.get('extract')
    if scenario_config.get('process'):
        deal_method = scenario_config.get('process')

    # 创建新的 DataFrame
    new_rows = []

    for idx, table in enumerate(tables, 1):
        log(f"正在处理第 {idx} 个表: {table}")

        # 复制模板行
        row = template_row.copy()

        # 更新关键字段
        row.iloc[0] = db_type.lower()  # 第1列：数据源类型
        row.iloc[1] = instance.lower()  # 第2列：实例
        row.iloc[2] = database.lower()  # 第3列：库
        row.iloc[3] = table.lower()     # 第4列：表
        row.iloc[12] = extract_method   # 第13列：抽数方式
        row.iloc[13] = deal_method      # 第14列：处理方式
        row.iloc[21] = f"input_{db_type.lower()}_{instance.lower()}_{database.lower()}"  # 第22列：抽数数据源

        # 应用异常场景
        action = scenario_config.get('action', {})
        if action:
            operation = action.get('operation')
            if operation == 'set_value':
                col_idx = action.get('column_index', 0)
                value = action.get('value', '')
                if col_idx < len(row):
                    row.iloc[col_idx] = value
                    log(f"  ⚠️ 应用异常场景: 列{col_idx}设置为'{value}'")
            elif operation == 'remove_column':
                col_idx = action.get('column_index', -1)
                if col_idx == -1:
                    col_idx = len(row) - 1
                if 0 <= col_idx < len(row):
                    col_name = df.columns[col_idx]
                    row.iloc[col_idx] = None
                    log(f"  ⚠️ 应用异常场景: 删除列{col_idx}({col_name})")

        log(f"  ✓ {table} 配置完成")

        new_rows.append(row)

    # 创建新的 DataFrame
    result_df = pd.DataFrame(new_rows, columns=df.columns)

    log("")
    log("字段更新完成！")
    log("")

    # 保存文件
    log(f"正在保存到: {OUTPUT_FILE}")
    result_df.to_excel(OUTPUT_FILE, index=False, engine='openpyxl')
    log("✓ 文件保存成功")
    log("")

    # 显示更新摘要
    log("=" * 70)
    log("更新摘要")
    log("=" * 70)
    log(f"数据源类型: {db_type}")
    log(f"实例: {instance}")
    log(f"库: {database}")
    log(f"表列表: {', '.join(tables)}")
    log(f"表数量: {len(tables)} 个")
    log(f"抽数方式: {extract_method} ({'全量' if extract_method == 'all' else '增量'})")
    log(f"处理方式: {deal_method} ({'覆盖' if deal_method == 'all' else '分区' if deal_method == 'ins' else '合并'})")
    log("=" * 70)
    log("")
    log(f"✅ 测试文件已生成: {OUTPUT_FILE}")
    log(f"   包含 {len(tables)} 行测试数据")
    log("")
    log("后续操作:")
    log("1. 调用批量上传接口:")
    log(f"   python batch_upload_validate.py \"{OUTPUT_FILE}\"")
    log("")

    return OUTPUT_FILE


def update_template(
    instance,
    database,
    table,
    db_type="mysql",
    extract_method="ins",
    deal_method="merge"
):
    """
    更新模板文件生成最新测试文件（单表模式，保留向后兼容）

    Args:
        instance: 实例名（如：cjjcommon）
        database: 数据库名（如：dataops_shitingjie）
        table: 表名（如：test_table_001）
        db_type: 数据库类型（mysql/tidb/adb），默认 mysql
        extract_method: 抽数方式（all=全量，ins=增量），默认 ins
        deal_method: 处理方式（all=覆盖，ins=分区，merge=合并），默认 merge

    Returns:
        str: 生成的文件路径
    """
    # 调用批量处理函数
    return update_template_batch(
        instance=instance,
        database=database,
        tables=[table],
        db_type=db_type,
        extract_method=extract_method,
        deal_method=deal_method
    )

    log("=" * 70)
    log("批量入仓测试文件模板更新器")
    log("=" * 70)
    log(f"模板文件: {os.path.basename(TEMPLATE_FILE)}")
    log(f"输出文件: {os.path.basename(OUTPUT_FILE)}")
    log("=" * 70)
    log("")

    # 检查模板文件是否存在
    if not os.path.exists(TEMPLATE_FILE):
        raise FileNotFoundError(f"模板文件不存在: {TEMPLATE_FILE}")

    # 读取模板文件
    log("正在读取模板文件...")
    df = pd.read_excel(TEMPLATE_FILE, engine='openpyxl')

    log(f"✓ 模板文件读取成功（{len(df)} 行 × {len(df.columns)} 列）")
    log("")

    # 更新字段（索引从0开始）
    log("正在更新字段...")

    # 第1列：数据源类型（索引0）
    old_db_type = df.iloc[0, 0]
    df.iloc[0, 0] = db_type.lower()
    log(f"  [列1] 数据源类型: {old_db_type} → {db_type}")

    # 第2列：实例（索引1）
    old_instance = df.iloc[0, 1]
    df.iloc[0, 1] = instance.lower()
    log(f"  [列2] 实例: {old_instance} → {instance}")

    # 第3列：库（索引2）
    old_database = df.iloc[0, 2]
    df.iloc[0, 2] = database.lower()
    log(f"  [列3] 库: {old_database} → {database}")

    # 第4列：表（索引3）
    old_table = df.iloc[0, 3]
    df.iloc[0, 3] = table.lower()
    log(f"  [列4] 表: {old_table} → {table}")

    # 第13列：抽数方式（索引12）
    old_extract = df.iloc[0, 12]
    df.iloc[0, 12] = extract_method
    log(f"  [列13] 抽数方式: {old_extract} → {extract_method}")

    # 第14列：处理方式（索引13）
    old_deal = df.iloc[0, 13]
    df.iloc[0, 13] = deal_method
    log(f"  [列14] 处理方式: {old_deal} → {deal_method}")

    # 第22列：抽数数据源（索引21）
    datasource = f"input_{db_type.lower()}_{instance.lower()}_{database.lower()}"
    old_datasource = df.iloc[0, 21]
    df.iloc[0, 21] = datasource
    log(f"  [列22] 抽数数据源: {old_datasource} → {datasource}")

    log("")
    log("字段更新完成！")
    log("")
    log(f"正在保存到: {OUTPUT_FILE}")
    df.to_excel(OUTPUT_FILE, index=False, engine='openpyxl')
    log("✓ 文件保存成功")
    log("")
    log("=" * 70)
    log("更新摘要")
    log("=" * 70)
    log(f"数据源类型: {db_type}")
    log(f"实例: {instance}")
    log(f"库: {database}")
    log(f"表: {table}")
    log(f"抽数方式: {extract_method} ({'全量' if extract_method == 'all' else '增量'})")
    log(f"处理方式: {deal_method} ({'覆盖' if deal_method == 'all' else '分区' if deal_method == 'ins' else '合并'})")
    log(f"抽数数据源: {datasource}")
    log("=" * 70)
    log("")
    log(f"✅ 测试文件已生成: {OUTPUT_FILE}")
    log("")
    log("后续操作:")
    log("1. 调用批量上传接口:")
    log(f"   python batch_upload_validate.py \"{OUTPUT_FILE}\"")
    log("")

    return OUTPUT_FILE


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description='批量入仓测试文件模板更新器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python template_updater.py cjjcommon dataops_shitingjie test_table_001
  python template_updater.py tidb-ares ares test_tidb_table --db-type tidb
  python template_updater.py cjjcommon dataops test_full --extract-method all --deal-method all
        """
    )

    parser.add_argument('instance', help='实例名（如：cjjcommon）')
    parser.add_argument('database', help='数据库名（如：dataops_shitingjie）')
    parser.add_argument('tables', nargs='+', help='表名')
    parser.add_argument('--db-type', default='mysql', choices=['mysql', 'tidb', 'adb'], help='数据库类型')
    parser.add_argument('--extract-method', default='ins', choices=['all', 'ins'], help='抽数方式')
    parser.add_argument('--deal-method', default='merge', choices=['all', 'ins', 'merge'], help='处理方式')
    parser.add_argument('--scenario', default='success', help='场景类型')

    args = parser.parse_args()

    valid_combinations = [
        ('all', 'all'),
        ('ins', 'merge'),
        ('ins', 'ins'),
    ]

    if (args.extract_method, args.deal_method) not in valid_combinations:
        output = {
            "status": "error",
            "error": "抽数方式和处理方式组合不合法",
            "valid_combinations": ["all+all", "ins+merge", "ins+ins"]
        }
        print("```json\n" + json.dumps(output, ensure_ascii=False, indent=2) + "\n```")
        sys.exit(1)

    try:
        output_file = update_template_batch(
            instance=args.instance,
            database=args.database,
            tables=args.tables,
            db_type=args.db_type,
            extract_method=args.extract_method,
            deal_method=args.deal_method,
            scenario=args.scenario
        )
        
        output = {
            "status": "success",
            "instances": [args.instance],
            "databases": [args.database],
            "tables": args.tables,
            "file_info": {
                "file_name": os.path.basename(output_file),
                "absolute_path": os.path.abspath(output_file),
                "relative_path": output_file,
                "table_count": len(args.tables)
            },
            "config": {
                "db_type": args.db_type,
                "scenario": args.scenario,
                "op_type": args.extract_method,
                "process_type": args.deal_method
            }
        }
        print("```json\n" + json.dumps(output, ensure_ascii=False, indent=2) + "\n```")
        sys.exit(0)
    except Exception as e:
        output = {
            "status": "error",
            "error": str(e)
        }
        print("```json\n" + json.dumps(output, ensure_ascii=False, indent=2) + "\n```")
        sys.exit(1)


if __name__ == '__main__':
    main()
