#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元数据完整性管理 Skill 入口
可以作为 Claude Code skill 使用，也可以独立运行
"""

import sys
import os
import argparse

# index.py 现在在 scripts 目录下，直接导入同目录的 metadata_complete
from metadata_complete import MetadataCompleteManager

# 数据库名到实例名的映射表
# 格式: {数据库名: [实例名列表]}
DATABASE_TO_INSTANCE_MAP = {
    'dataops_shitingjie': ['cjjcommon'],
    'dataops': ['bigdata-biz'],
    'datagovernor': ['bigdata-biz'],
    'datahub': ['cjjloan'],
    'stjtestadb': ['sitadbrealtimedw'],
    'ares': ['sitpublic']
}


def infer_instance_from_database(database: str) -> str:
    """
    根据数据库名推断实例名

    Args:
        database: 数据库名称

    Returns:
        实例名，如果无法推断则返回 None

    Raises:
        ValueError: 如果数据库名在多个实例中存在
    """
    if database not in DATABASE_TO_INSTANCE_MAP:
        return None

    instances = DATABASE_TO_INSTANCE_MAP[database]

    if len(instances) > 1:
        raise ValueError(
            f"数据库 '{database}' 存在于多个实例中: {', '.join(instances)}\n"
            f"请使用 --instance 参数明确指定实例"
        )

    return instances[0]


def main():
    """主函数 - 用于 Claude Code skill 调用和独立运行"""

    parser = argparse.ArgumentParser(
        description='元数据完整性管理 - 自动化执行 MySQL 库表元数据管理流程'
    )

    parser.add_argument(
        '--instance',
        required=False,
        help='MySQL 实例标识（如：cjjcommon）。如不提供，将根据数据库名自动推断'
    )

    parser.add_argument(
        '--database',
        required=True,
        help='数据库名称（如：dataops_shitingjie）'
    )

    parser.add_argument(
        '--table',
        required=True,
        help='数据表名称（如：0418bugfuxianccc）'
    )

    parser.add_argument(
        '--existUpdate',
        default='true',
        choices=['true', 'false'],
        help='是否存在更新操作（默认：true）'
    )

    parser.add_argument(
        '--existDelete',
        default='false',
        choices=['true', 'false'],
        help='是否存在删除操作（默认：false）'
    )

    args = parser.parse_args()

    # 如果没有提供实例名，尝试自动推断
    instance = args.instance
    if not instance:
        try:
            instance = infer_instance_from_database(args.database)
            if instance:
                print(f"\n✓ 根据数据库名 '{args.database}' 自动推断实例: {instance}")
            else:
                print(f"\n✗ 错误: 无法从数据库名 '{args.database}' 推断实例")
                print(f"支持的数据库: {', '.join(DATABASE_TO_INSTANCE_MAP.keys())}")
                print(f"请使用 --instance 参数明确指定实例")
                return 1
        except ValueError as e:
            print(f"\n✗ 错误: {str(e)}")
            return 1

    # 转换 string 为 boolean
    exist_update = args.existUpdate.lower() == 'true'
    exist_delete = args.existDelete.lower() == 'true'

    # 固定的人员信息
    P_N = "施婷杰"
    P_U = "71e8b23d-45e2-497a-b247-f5b807fb4f65"

    # 打印配置信息
    print("\n" + "="*70)
    print("元数据完整性管理 Skill")
    print("="*70)
    print(f"实例: {instance}")
    print(f"数据库: {args.database}")
    print(f"表: {args.table}")
    print(f"人员: {P_N}")
    print(f"更新操作: {'支持' if exist_update else '不支持'}")
    print(f"删除操作: {'支持' if exist_delete else '不支持'}")
    print("="*70)
    print()

    try:
        # 创建管理器并执行
        manager = MetadataCompleteManager()

        success = manager.complete_metadata(
            instance=instance,
            database=args.database,
            table=args.table,
            p_n=P_N,
            p_u=P_U,
            exist_update=exist_update,
            exist_delete=exist_delete
        )

        if success:
            print("\n" + "="*70)
            print("✓ Skill 执行成功！")
            print("="*70)
            return 0
        else:
            print("\n" + "="*70)
            print("✗ Skill 执行失败！")
            print("="*70)
            return 1

    except Exception as e:
        print(f"\n✗ 发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
