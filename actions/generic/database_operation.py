"""数据库操作动作（通用动作）

设计理念：
- 提供通用的数据库操作能力（增删改查）
- 支持多种数据库（MySQL等）
- 自动处理连接、事务、参数绑定等细节
- 支持变量替换（从上下文获取参数）
"""
from typing import Any, Dict, List
from actions.action_registry import action_registry
from actions.base import ExecutionAction, ActionMetadata
from utils.database import DatabaseConnection


@action_registry.register_decorator()
class DatabaseInsertAction(ExecutionAction):
    """
    数据库插入动作
    """

    metadata = ActionMetadata(
        name='database_insert',
        category='database',
        description='向数据库表插入数据',
        parameters=[
            {
                'name': 'database',
                'type': 'str',
                'required': True,
                'description': '数据库名称'
            },
            {
                'name': 'table',
                'type': 'str',
                'required': True,
                'description': '表名'
            },
            {
                'name': 'data',
                'type': 'dict or list',
                'required': True,
                'description': '要插入的数据（单条记录用dict，多条记录用list）'
            }
        ],
        returns={
            'inserted_count': '插入的记录数'
        },
        examples=[
            {
                'description': '插入单条记录',
                'code': '''database_insert(
    database="copilot",
    table="common_job_status",
    data={
        "job_name": "AiScriptUidPullJob",
        "business_type": "postLoan",
        "status": "FAIL",
        "complete_count": 2
    }
)'''
            },
            {
                'description': '插入多条记录',
                'code': '''database_insert(
    database="copilot",
    table="ai_script_recommendation_log",
    data=[
        {"source": "postLoan", "execute_status": "INIT"},
        {"source": "postLoan", "execute_status": "INIT"}
    ]
)'''
            }
        ]
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        """执行数据库插入"""
        self.validate_parameters(params)

        database = params['database']
        table = params['table']
        data = params['data']

        # 统一处理为列表
        if isinstance(data, dict):
            data_list = [data]
        elif isinstance(data, list):
            data_list = data
        else:
            raise ValueError(f"data参数必须是dict或list类型，实际类型: {type(data)}")

        if not data_list:
            return {
                'status': 'SUCCESS',
                'inserted_count': 0,
                'message': '没有数据需要插入'
            }

        inserted_count = 0

        for record in data_list:
            try:
                # 构建INSERT语句
                columns = list(record.keys())
                placeholders = ', '.join(['%s'] * len(columns))
                column_names = ', '.join(columns)

                sql = f"""
                    INSERT INTO {database}.{table} ({column_names})
                    VALUES ({placeholders})
                """

                values = tuple(record[col] for col in columns)

                # 执行插入
                DatabaseConnection.execute_update(database, sql, values)
                inserted_count += 1

            except Exception as e:
                print(f"    ⚠️  插入记录失败: {e}")
                print(f"    记录: {record}")
                # 继续处理下一条记录

        return {
            'status': 'SUCCESS' if inserted_count > 0 else 'FAIL',
            'inserted_count': inserted_count,
            'message': f'成功插入 {inserted_count}/{len(data_list)} 条记录'
        }


@action_registry.register_decorator()
class DatabaseDeleteAction(ExecutionAction):
    """数据库删除动作 (支持单表或多表)"""

    metadata = ActionMetadata(
        name='database_delete',
        category='database',
        description='根据 SQL 条件字符串删除一个或多个表中的记录',
        parameters=[
            {
                'name': 'database',
                'type': 'str',
                'required': True,
                'description': '数据库名称'
            },
            {
                'name': 'table',
                'type': 'str or list',
                'required': True,
                'description': '表名（单表传字符串，多表传列表，如 ["table1", "table2"]）'
            },
            {
                'name': 'where',
                'type': 'str',
                'required': True,
                'description': 'SQL WHERE 子句字符串（不包含 WHERE 关键字，例如 "uid = \'504\'"）'
            }
        ],
        returns={
            'total_deleted_count': '所有表累计删除的记录总数',
            'detail': '各表删除详情'
        },
        examples=[
            {
                'description': '同时清理多张表中的同一用户数据',
                'code': '''database_delete(
    database="copilot",
    table=["ai_script_recommendation_log", "ai_script_recommendation"],
    where="uid = '504ac82116e611f1bb119c63c059e356'"
)'''
            }
        ]
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        """执行数据库删除"""
        self.validate_parameters(params)

        database = params['database']
        table_param = params['table']
        where = params['where']

        # 安全校验：防止空条件误删
        if not where or not isinstance(where, str) or not where.strip():
            return {
                'status': 'FAIL',
                'total_deleted_count': 0,
                'message': '删除条件(where)不能为空，拒绝执行全表删除'
            }

        # 统一转换为列表处理
        tables = [table_param] if isinstance(table_param, str) else table_param

        total_deleted_count = 0
        detail = {}

        for table in tables:
            try:
                sql = f"DELETE FROM {database}.{table} WHERE {where}"
                # 执行删除并获取受影响行数
                count = DatabaseConnection.execute_update(database, sql, ())

                total_deleted_count += count
                print(f"    ✅  从表 {table} 删除了 {count} 条记录")
                detail[table] = {"status": "SUCCESS", "count": count}

            except Exception as e:
                print(f"    ⚠️  从表 {table} 删除数据失败: {e}")
                detail[table] = {"status": "FAIL", "error": str(e)}

        # 判定最终状态：如果所有表都尝试过且没有发生严重中断则为 SUCCESS
        status = "SUCCESS" if any(d["status"] == "SUCCESS" for d in detail.values()) else "FAIL"

        return {
            'status': status,
            'total_deleted_count': total_deleted_count,
            'detail': detail,
            'message': f'共从 {len(tables)} 张表中删除 {total_deleted_count} 条记录'
        }


@action_registry.register_decorator()
class DatabaseUpdateAction(ExecutionAction):
    """数据库更新动作"""

    metadata = ActionMetadata(
        name='database_update',
        category='database',
        description='根据 SQL 条件字符串更新数据库表中的数据',
        parameters=[
            {
                'name': 'database',
                'type': 'str',
                'required': True,
                'description': '数据库名称'
            },
            {
                'name': 'table',
                'type': 'str',
                'required': True,
                'description': '表名'
            },
            {
                'name': 'data',
                'type': 'dict',
                'required': True,
                'description': '要更新的字段及其新值（字典格式，如 {"status": "SUCCESS"}）'
            },
            {
                'name': 'where',
                'type': 'str',
                'required': True,
                'description': 'SQL WHERE 子句字符串（不包含 WHERE 关键字，例如 "serial_id = \'123\'"）'
            }
        ],
        returns={
            'updated_count': '受影响（被更新）的记录数'
        },
        examples=[
            {
                'description': '更新指定流水号的执行状态',
                'code': '''database_update(
    database="copilot",
    table="ai_script_recommendation_log",
    data={
        "execute_status": "SUCCESS",
        "output_data": "{\\"script\\": \\"Hello\\"}"
    },
    where="serial_id = 'c96660e776d84955b810a83da5b18767='"
)'''
            }
        ]
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        """执行数据库更新"""
        self.validate_parameters(params)

        database = params['database']
        table = params['table']
        data = params['data']
        where = params['where']

        # 安全校验：防止空条件导致全表更新
        if not where or not isinstance(where, str) or not where.strip():
            return {
                'status': 'FAIL',
                'updated_count': 0,
                'message': '更新条件(where)不能为空，拒绝执行全表更新操作'
            }

        # 校验更新数据非空
        if not data or not isinstance(data, dict):
            return {
                'status': 'FAIL',
                'updated_count': 0,
                'message': '更新内容(data)必须为非空字典'
            }

        try:
            # 构建 SET 子句，使用占位符防止 SQL 注入
            columns = list(data.keys())
            set_clause = ', '.join([f"{col} = %s" for col in columns])
            values = tuple(data[col] for col in columns)

            # 拼接最终 SQL
            sql = f"UPDATE {database}.{table} SET {set_clause} WHERE {where}"

            # 执行更新
            updated_count = DatabaseConnection.execute_update(database, sql, values)

            return {
                'status': 'SUCCESS',
                'updated_count': updated_count,
                'message': f'成功在 {database}.{table} 中更新了 {updated_count} 条记录'
            }

        except Exception as e:
            print(f"    ⚠️  更新记录失败: {e}")
            print(f"    SQL: UPDATE {database}.{table} SET ... WHERE {where}")
            return {
                'status': 'FAIL',
                'updated_count': 0,
                'message': f'执行更新时发生异常: {str(e)}'
            }


@action_registry.register_decorator()
class DatabaseSelectAction(ExecutionAction):
    """数据库查询动作"""

    metadata = ActionMetadata(
        name='database_select',
        category='database',
        description='根据 SQL 条件查询数据库表中的数据',
        parameters=[
            {
                'name': 'database',
                'type': 'str',
                'required': True,
                'description': '数据库名称'
            },
            {
                'name': 'table',
                'type': 'str',
                'required': True,
                'description': '表名'
            },
            {
                'name': 'fields',
                'type': 'str or list',
                'required': False,
                'description': '查询字段，默认为 "*"。支持列表格式 ["id", "name"] 或字符串 "id, name"'
            },
            {
                'name': 'where',
                'type': 'str',
                'required': False,
                'description': 'SQL WHERE 子句字符串（不包含 WHERE 关键字，例如 "uid = \'123\'"）'
            },
            {
                'name': 'order_by',
                'type': 'str',
                'required': False,
                'description': '排序规则（不包含 ORDER BY 关键字，例如 "created_at DESC"）'
            },
            {
                'name': 'limit',
                'type': 'int',
                'required': False,
                'description': '限制返回条数，默认为 100'
            }
        ],
        returns={
            'status': 'SUCCESS/FAIL',
            'records': '查询到的记录列表（List[Dict]）',
            'count': '返回的记录数量'
        },
        examples=[
            {
                'description': '查询指定用户的最新一条日志',
                'code': '''database_select(
    database="copilot",
    table="ai_script_recommendation_log",
    where="uid = '504ac82116e611f1bb119c63c059e356'",
    order_by="created_at DESC",
    limit=1
)'''
            },
            {
                'description': '查询指定表的特定字段',
                'code': '''database_select(
    database="copilot",
    table="common_job_status",
    fields=["job_name", "status"],
    where="status = 'FAIL'"
)'''
            }
        ]
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        """执行数据库查询"""
        self.validate_parameters(params)

        database = params['database']
        table = params['table']
        fields_param = params.get('fields', '*')
        where = params.get('where')
        order_by = params.get('order_by')
        limit = params.get('limit', 100)

        # 1. 处理查询字段
        if isinstance(fields_param, list):
            fields_sql = ", ".join(fields_param)
        else:
            fields_sql = fields_param

        # 2. 构建基础 SQL
        sql = f"SELECT {fields_sql} FROM {database}.{table}"

        # 3. 拼接可选子句
        if where and where.strip():
            sql += f" WHERE {where}"

        if order_by and order_by.strip():
            sql += f" ORDER BY {order_by}"

        if limit and limit > 0:
            sql += f" LIMIT {limit}"

        try:
            # 执行查询
            records = DatabaseConnection.execute_query(database, sql)

            count = len(records) if records else 0
            print(f"    ✅  从表 {table} 查询成功，获取到 {count} 条记录")

            return {
                'status': 'SUCCESS',
                'records': records,
                'count': count,
                'message': f'成功从 {database}.{table} 查询到 {count} 条数据'
            }

        except Exception as e:
            print(f"    ⚠️  查询数据库失败: {e}")
            print(f"    SQL: {sql}")
            return {
                'status': 'FAIL',
                'records': [],
                'count': 0,
                'message': f'执行查询时发生异常: {str(e)}'
            }