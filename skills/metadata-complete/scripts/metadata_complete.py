"""
MySQL 库表元数据完整性管理脚本
功能：串联调用 GET 和 POST 接口，实现元数据查询和管理的自动化流程
"""

import requests
import json
from typing import Dict, List, Any, Optional


class MetadataCompleteManager:
    """MySQL 库表元数据完整性管理器"""

    def __init__(self, base_url: str = "http://firekylin.apps01.ali-bj-sit03.shuheo.net"):
        """
        初始化管理器

        Args:
            base_url: 接口基础 URL
        """
        self.base_url = base_url
        self.get_url = f"{base_url}/firekylin/mysql-metadata/mysql/table/metadata"
        self.post_url = f"{base_url}/firekylin/mysql-metadata/mysql/table/metadata:manage"

    def get_metadata(self, instance: str, database: str, table: str,
                     p_n: str, p_u: str) -> Optional[Dict[str, Any]]:
        """
        步骤1：调用 GET 接口查询库表元数据

        Args:
            instance: MySQL 实例标识
            database: 数据库名称
            table: 数据表名称
            p_n: 人员名称
            p_u: 人员唯一标识

        Returns:
            元数据响应字典，失败返回 None
        """
        params = {
            "instance": instance,
            "database": database,
            "table": table,
            "p_n": p_n,
            "p_u": p_u
        }

        try:
            print(f"[GET] 正在查询元数据...")
            print(f"  实例: {instance}")
            print(f"  数据库: {database}")
            print(f"  表: {table}")

            response = requests.get(self.get_url, params=params, timeout=30)

            print(f"[GET] 状态码: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"[GET] 成功获取元数据")
                return data
            else:
                print(f"[GET] 请求失败: {response.text}")
                return None

        except Exception as e:
            print(f"[GET] 发生异常: {str(e)}")
            return None

    def supplement_column_metadata(self, column_metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        步骤2：补充 columnMetadata 的 5 个固定字段

        Args:
            column_metadata: 原始列元数据数组

        Returns:
            补充后的列元数据数组
        """
        supplemented_metadata = []

        for column in column_metadata:
            # 复制原有字段
            new_column = column.copy()

            # 补充 5 个固定字段（如果不存在则添加）
            if 'canNotBeModified' not in new_column:
                new_column['canNotBeModified'] = False
            if 'columnEditing' not in new_column:
                new_column['columnEditing'] = False
            if 'sensitive' not in new_column:
                new_column['sensitive'] = False
            if 'json' not in new_column:
                new_column['json'] = False
            if 'enumerated' not in new_column:
                new_column['enumerated'] = False

            supplemented_metadata.append(new_column)

        print(f"[处理] 已为 {len(supplemented_metadata)} 个字段补充固定属性")
        return supplemented_metadata

    def manage_metadata(self, instance: str, database: str, p_n: str, p_u: str,
                       table_name: str, exist_update: bool, exist_delete: bool,
                       column_metadata: List[Dict[str, Any]]) -> bool:
        """
        步骤3：调用 POST 接口管理库表元数据

        Args:
            instance: MySQL 实例标识（与 GET 一致）
            database: 数据库名称（与 GET 一致）
            p_n: 人员名称（与 GET 一致）
            p_u: 人员唯一标识（与 GET 一致）
            table_name: 表名称（来自 GET 响应）
            exist_update: 是否存在更新操作
            exist_delete: 是否存在删除操作
            column_metadata: 补充后的列元数据数组

        Returns:
            是否成功
        """
        # Query 参数（与 GET 一致，不含 table）
        params = {
            "instance": instance,
            "database": database,
            "p_n": p_n,
            "p_u": p_u
        }

        # Body 参数
        body = {
            "tableName": table_name,
            "existUpdate": exist_update,
            "existDelete": exist_delete,
            "columnMetadata": column_metadata
        }

        try:
            print(f"[POST] 正在管理元数据...")
            print(f"  表名: {table_name}")
            print(f"  existUpdate: {exist_update}")
            print(f"  existDelete: {exist_delete}")
            print(f"  字段数量: {len(column_metadata)}")

            headers = {
                "Content-Type": "application/json"
            }

            response = requests.post(
                self.post_url,
                params=params,
                json=body,
                headers=headers,
                timeout=30
            )

            print(f"[POST] 状态码: {response.status_code}")

            if response.status_code == 200:
                print(f"[POST] 元数据管理成功")
                print(f"[POST] 响应: {response.text}")
                return True
            else:
                print(f"[POST] 请求失败: {response.text}")
                return False

        except Exception as e:
            print(f"[POST] 发生异常: {str(e)}")
            return False

    def complete_metadata(self, instance: str, database: str, table: str,
                         p_n: str, p_u: str,
                         exist_update: bool = True,
                         exist_delete: bool = False) -> bool:
        """
        完整的元数据管理流程：GET -> 处理 -> POST

        Args:
            instance: MySQL 实例标识
            database: 数据库名称
            table: 数据表名称
            p_n: ���员名称
            p_u: 人员唯一标识
            exist_update: 是否存在更新操作（默认 True）
            exist_delete: 是否存在删除操作（默认 True）

        Returns:
            是否成功完成整个流程
        """
        print("="*60)
        print("开始执行元数据完整性管理流程")
        print("="*60)

        # 步骤1：调用 GET 接口
        metadata = self.get_metadata(instance, database, table, p_n, p_u)
        if not metadata:
            print("[错误] GET 接口调用失败，流程终止")
            return False

        # 提取核心参数
        table_name = metadata.get('tableName')
        column_metadata = metadata.get('columnMetadata', [])

        if not table_name:
            print("[错误] GET 响应中缺少 tableName，流程终止")
            return False

        if not column_metadata:
            print("[警告] GET 响应中 columnMetadata 为空")

        print("-"*60)

        # 步骤2：补充字段
        supplemented_metadata = self.supplement_column_metadata(column_metadata)

        print("-"*60)

        # 步骤3：调用 POST 接口
        success = self.manage_metadata(
            instance=instance,
            database=database,
            p_n=p_n,
            p_u=p_u,
            table_name=table_name,
            exist_update=exist_update,
            exist_delete=exist_delete,
            column_metadata=supplemented_metadata
        )

        print("="*60)
        if success:
            print("元数据完整性管理流程执行成功！")
        else:
            print("元数据完整性管理流程执行失败！")
        print("="*60)

        return success


def main():
    """主函数：使用命令行参数或测试数据执行元数据完整性管理"""
    import argparse

    parser = argparse.ArgumentParser(description='MySQL 元数据完整性管理')
    parser.add_argument('--instance', '-i', type=str, help='MySQL 实例标识')
    parser.add_argument('--database', '-d', type=str, help='数据库名称')
    parser.add_argument('--table', '-t', type=str, help='数据表名称')
    parser.add_argument('--owner-name', '-n', type=str, help='人员名称')
    parser.add_argument('--owner-id', '-u', type=str, help='人员唯一标识')
    parser.add_argument('--base-url', '-b', type=str,
                        default='http://firekylin.apps01.ali-bj-sit03.shuheo.net',
                        help='API 基础 URL（默认：http://firekylin.apps01.ali-bj-sit03.shuheo.net）')
    args = parser.parse_args()

    # 如果没有命令行参数，使用硬编码的测试数据（兼容旧调用方式）
    instance = args.instance or "cjjcommon"
    database = args.database or "dataops_shitingjie"
    table = args.table or "0418bugfuxianccc"
    p_n = args.owner_name or "施婷杰"
    p_u = args.owner_id or "71e8b23d-45e2-497a-b247-f5b807fb4f65"

    # 创建管理器（允许通过命令行参数覆盖 base_url）
    manager = MetadataCompleteManager(base_url=args.base_url)

    # 执行完整流程（使用默认值：更新=True，删除=False）
    success = manager.complete_metadata(
        instance=instance,
        database=database,
        table=table,
        p_n=p_n,
        p_u=p_u,
        exist_update=True,   # 是否存在更新操作
        exist_delete=False   # 是否存在删除操作
    )

    return success


if __name__ == "__main__":
    main()
