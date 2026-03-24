"""
批量执行脚本：批量处理多个表的元数据完整性管理

使用场景：
- 需要对同一数据库下的多个表执行元数据管理
- 需要对多个数据库的多个表执行元数据管理

使用方法：
1. 通过命令行参数指定表列表
2. 格式：-t instance:database:table 或 -i instance -d database -t table1 -t table2
3. 运行脚本

注意：
- p_n 和 p_u 已固定为"施婷杰"和对应的 UUID
- 默认 existUpdate=True, existDelete=False
- 如需支持删除操作，使用 --exist-delete 参数

快捷命令示例：
    # 同一数据库的多个表
    python batch_process.py -i cjjcommon -d dataops_shitingjie -t table1 -t table2

    # 不同数据库的表（使用完整格式）
    python batch_process.py -t cjjcommon:dataops_shitingjie:table1 -t cjjcommon:dataops:table2
"""

import sys
import os
import argparse
from typing import List, Dict, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from metadata_complete import MetadataCompleteManager


def batch_process(table_list: List[Tuple[str, str, str]], exist_update: bool = True, exist_delete: bool = False):
    """批量处理多个表的元数据完整性管理

    Args:
        table_list: 表列表，每个元素是 (instance, database, table) 元组
        exist_update: 是否存在更新操作
        exist_delete: 是否存在删除操作
    """
    # 固定的人员信息
    P_N = "施婷杰"
    P_U = "71e8b23d-45e2-497a-b247-f5b807fb4f65"

    print("="*70)
    print("批量执行：元数据完整性管理")
    print(f"总共 {len(table_list)} 个表待处理")
    print(f"更新操作: {'支持' if exist_update else '不支持'}")
    print(f"删除操作: {'支持' if exist_delete else '不支持'}")
    print("="*70)
    print()

    # 创建管理器
    manager = MetadataCompleteManager()

    # 记录结果
    success_count = 0
    fail_count = 0
    results: List[Tuple[str, str, str, bool]] = []

    # 逐个处理
    for idx, (instance, database, table) in enumerate(table_list, 1):
        print(f"\n{'='*70}")
        print(f"处理进度: {idx}/{len(table_list)}")
        print(f"{'='*70}")

        success = manager.complete_metadata(
            instance=instance,
            database=database,
            table=table,
            p_n=P_N,
            p_u=P_U,
            exist_update=exist_update,
            exist_delete=exist_delete
        )

        results.append((instance, database, table, success))

        if success:
            success_count += 1
        else:
            fail_count += 1

    # 打印汇总报告
    print("\n" + "="*70)
    print("批量处理完成 - 汇总报告")
    print("="*70)
    print(f"总计: {len(table_list)} 个表")
    print(f"成功: {success_count} 个")
    print(f"失败: {fail_count} 个")
    print("-"*70)

    # 打印详细结果
    print("详细结果：")
    for instance, database, table, success in results:
        status = "✓ 成功" if success else "✗ 失败"
        print(f"  {status}  {instance}.{database}.{table}")

    print("="*70)

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='批量处理多个表的元数据完整性管理')
    parser.add_argument('-i', '--instance', type=str, help='MySQL 实例标识（如：cjjcommon）')
    parser.add_argument('-d', '--database', type=str, help='数据库名称（如：dataops_shitingjie）')
    parser.add_argument('-t', '--table', type=str, action='append', required=True,
                        help='数据表名称，可多次使用（如：-t table1 -t table2）')
    parser.add_argument('--exist-update', dest='exist_update', action='store_true', default=True,
                        help='是否存在更新操作（默认：True）')
    parser.add_argument('--no-exist-update', dest='exist_update', action='store_false',
                        help='禁用更新操作')
    parser.add_argument('--exist-delete', dest='exist_delete', action='store_true', default=False,
                        help='是否支持删除操作（默认：False）')

    args = parser.parse_args()

    table_list = []
    for table_item in args.table:
        if ':' in table_item:
            parts = table_item.split(':')
            if len(parts) == 3:
                table_list.append((parts[0], parts[1], parts[2]))
            else:
                print(f"[警告] 忽略无效格式: {table_item}，格式应为 instance:database:table")
        else:
            if args.instance and args.database:
                table_list.append((args.instance, args.database, table_item))
            else:
                print("[警告] 忽略无效表: {}，需要指定 -i 和 -d 参数".format(table_item))

    if not table_list:
        print("[错误] 请至少指定一个有效的表")
        sys.exit(1)

    exit_code = batch_process(
        table_list=table_list,
        exist_update=args.exist_update,
        exist_delete=args.exist_delete
    )
    sys.exit(exit_code)
