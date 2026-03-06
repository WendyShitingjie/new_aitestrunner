"""
数据库断言动作集 - 增强版 (支持超时轮询)

设计原则：
1. 职责分离：动作负责查库取值，AssertionEngine 负责逻辑比较。
2. 参数规范：database 必传且位于 table 之前。
3. 轮询支持：增加 timeout 和 interval 参数，适配异步 Job 执行等待场景。
"""
import time
from typing import Any, Dict, List
from actions.action_registry import action_registry
from actions.base import ExecutionAction, ActionMetadata
from utils.database import DatabaseConnection
from utils.assertion_engine import AssertionEngine


@action_registry.register_decorator()
class AssertDatabaseFieldAction(ExecutionAction):
    """单记录字段断言动作 (支持轮询)"""

    metadata = ActionMetadata(
        name='assert_database_field',
        category='assertion',
        description='断言数据库指定记录的字段满足特定条件（支持超时轮询）',
        parameters=[
            {'name': 'database', 'type': 'str', 'required': True, 'description': '数据库名称'},
            {'name': 'table', 'type': 'str', 'required': True, 'description': '表名'},
            {'name': 'field', 'type': 'str', 'required': True, 'description': '字段名'},
            {'name': 'where', 'type': 'str', 'required': True, 'description': 'WHERE子句'},
            {'name': 'expected', 'type': 'any', 'required': False, 'description': '期望值'},
            {'name': 'operator', 'type': 'str', 'required': False, 'default': '等于', 'description': '比较符'},
            {'name': 'timeout', 'type': 'int', 'required': False, 'default': 0, 'description': '最大超时时间(秒)，0表示不轮询'},
            {'name': 'interval', 'type': 'int', 'required': False, 'default': 2, 'description': '轮询间隔(秒)'}
        ],
        returns={
            'status': 'PASS/FAIL',
            'reason': '结果描述',
            'details': '详情'
        }
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        self.validate_parameters(params)
        db, table, field, where = params['database'], params['table'], params['field'], params['where']
        expected, operator = params.get('expected'), params.get('operator', 'eq')
        timeout, interval = params.get('timeout', 0), params.get('interval', 2)

        sql = f"SELECT {field} FROM {table} WHERE {where} LIMIT 1"
        start_time = time.time()
        attempt = 0
        last_actual = None
        # print(f"sql: {sql}")
        while True:
            attempt += 1
            try:
                results = DatabaseConnection.execute_query(db, sql)
                actual = results[0][field] if results else None
                last_actual = actual

                is_pass = AssertionEngine.compare(actual, expected, operator)
                if is_pass:
                    return {
                        'status': 'PASS',
                        'reason': f"字段 [{field}] 校验成功 (尝试 {attempt} 次)：实际值 '{actual}' {AssertionEngine.get_desc(operator)} '{expected}'",
                        'details': {'actual': actual, 'expected': expected, 'sql': sql, 'attempts': attempt}
                    }
            except Exception as e:
                # 查询异常且未设置超时，则立即报错
                if timeout <= 0:
                    return {'status': 'FAIL', 'reason': f"查询异常: {str(e)}"}

            # 轮询判定
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                break

            print(f"    ⏳ [assert_database_field] 第 {attempt} 次不匹配，等待轮询... (已耗时 {round(elapsed, 1)}s)")
            time.sleep(interval)

        return {
            'status': 'FAIL',
            'reason': f"字段 [{field}] 校验超时失败：最终实际值 '{last_actual}' 不满足条件",
            'details': {'actual': last_actual, 'expected': expected, 'timeout': timeout, 'attempts': attempt}
        }


@action_registry.register_decorator()
class AssertDatabaseRecordCountAction(ExecutionAction):
    """记录数断言动作 (支持轮询)"""

    metadata = ActionMetadata(
        name='assert_database_record_count',
        category='assertion',
        description='断言符合条件的数据库记录行数是否达标（支持超时轮询）',
        parameters=[
            {'name': 'database', 'type': 'str', 'required': True, 'description': '数据库名称'},
            {'name': 'table', 'type': 'str', 'required': True, 'description': '表名'},
            {'name': 'where', 'type': 'str', 'required': True, 'description': 'WHERE条件'},
            {'name': 'expected', 'type': 'int', 'required': True, 'description': '期望行数'},
            {'name': 'operator', 'type': 'str', 'required': False, 'default': '>=', 'description': '比较符'},
            {'name': 'timeout', 'type': 'int', 'required': False, 'default': 0, 'description': '最大超时时间(秒)'},
            {'name': 'interval', 'type': 'int', 'required': False, 'default': 2, 'description': '轮询间隔(秒)'}
        ],
        returns={
            'status': 'PASS/FAIL',
            'reason': '结果描述',
            'details': '详情'
        }
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        db, table, where = params['database'], params['table'], params['where']
        expected, operator = params['expected'], params.get('operator', 'ge')
        timeout, interval = params.get('timeout', 0), params.get('interval', 2)

        sql = f"SELECT COUNT(*) as count FROM {table} WHERE {where}"
        start_time = time.time()
        attempt = 0
        last_actual = 0

        while True:
            attempt += 1
            results = DatabaseConnection.execute_query(db, sql)
            actual = results[0]['count']
            last_actual = actual

            is_pass = AssertionEngine.compare(actual, expected, operator)
            if is_pass:
                return {
                    'status': 'PASS',
                    'reason': f"行数校验成功 (尝试 {attempt} 次)：实际 {actual} {AssertionEngine.get_desc(operator)} {expected}",
                    'details': {'actual': actual, 'expected': expected, 'attempts': attempt}
                }

            elapsed = time.time() - start_time
            if elapsed >= timeout:
                break
            time.sleep(interval)

        return {
            'status': 'FAIL',
            'reason': f"行数校验超时失败：最终行数 {last_actual} 不满足期望",
            'details': {'actual': last_actual, 'expected': expected, 'timeout': timeout}
        }


@action_registry.register_decorator()
class AssertDatabaseAllMatchAction(ExecutionAction):
    """批量记录一致性断言动作 (支持轮询)"""

    metadata = ActionMetadata(
        name='assert_database_all_match',
        category='assertion',
        description='断言查询出的所有记录的指定字段是否全部满足条件（支持超时轮询）',
        parameters=[
            {'name': 'database', 'type': 'str', 'required': True, 'description': '数据库名称'},
            {'name': 'table', 'type': 'str', 'required': True, 'description': '表名'},
            {'name': 'field', 'type': 'str', 'required': True, 'description': '字段名'},
            {'name': 'where', 'type': 'str', 'required': True, 'description': 'WHERE条件'},
            {'name': 'expected', 'type': 'any', 'required': True, 'description': '期望值'},
            {'name': 'operator', 'type': 'str', 'required': False, 'default': '等于'},
            {'name': 'timeout', 'type': 'int', 'required': False, 'default': 0},
            {'name': 'interval', 'type': 'int', 'required': False, 'default': 2}
        ],
        returns={
            'status': 'PASS/FAIL',
            'reason': '结果描述',
            'details': '详情'
        }
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        db, table, field, where = params['database'], params['table'], params['field'], params['where']
        expected, operator = params['expected'], params.get('operator', 'eq')
        timeout, interval = params.get('timeout', 0), params.get('interval', 2)

        sql = f"SELECT {field} FROM {table} WHERE {where}"
        start_time = time.time()
        attempt = 0

        while True:
            attempt += 1
            results = DatabaseConnection.execute_query(db, sql)
            if results:
                mismatched = [r[field] for r in results if not AssertionEngine.compare(r[field], expected, operator)]
                if not mismatched:
                    return {
                        'status': 'PASS',
                        'reason': f"全量校验成功：共 {len(results)} 条记录全部匹配成功"
                    }

            elapsed = time.time() - start_time
            if elapsed >= timeout:
                break
            time.sleep(interval)

        return {'status': 'FAIL', 'reason': f"全量校验超时：部分或全部记录不满足条件"}


@action_registry.register_decorator()
class AssertDatabaseJsonFieldAction(ExecutionAction):
    """JSON字段内容断言动作 (支持轮询)"""

    metadata = ActionMetadata(
        name='assert_database_json_field',
        category='assertion',
        description='断言数据库中JSON列内的指定路径值是否满足条件（支持超时轮询）',
        parameters=[
            {'name': 'database', 'type': 'str', 'required': True, 'description': '数据库名称'},
            {'name': 'table', 'type': 'str', 'required': True, 'description': '表名'},
            {'name': 'field', 'type': 'str', 'required': True, 'description': 'JSON列名'},
            {'name': 'path', 'type': 'str', 'required': True, 'description': 'JSON路径'},
            {'name': 'where', 'type': 'str', 'required': True, 'description': 'WHERE条件'},
            {'name': 'expected', 'type': 'any', 'required': False},
            {'name': 'operator', 'type': 'str', 'required': False, 'default': '不为空'},
            {'name': 'timeout', 'type': 'int', 'required': False, 'default': 0},
            {'name': 'interval', 'type': 'int', 'required': False, 'default': 2}
        ],
        returns={
            'status': 'PASS/FAIL',
            'reason': '结果描述',
            'details': '详情'
        }
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        db, table, j_col, path = params['database'], params['table'], params['field'], params['path']
        where = params['where']
        expected, operator = params.get('expected'), params.get('operator', 'not_null')
        timeout, interval = params.get('timeout', 0), params.get('interval', 2)

        sql = f"SELECT JSON_EXTRACT({j_col}, '{path}') as val FROM {table} WHERE {where} LIMIT 1"
        start_time = time.time()
        attempt = 0
        last_actual = None

        while True:
            attempt += 1
            results = DatabaseConnection.execute_query(db, sql)
            raw_val = results[0]['val'] if results else None
            actual = raw_val
            if isinstance(raw_val, str) and raw_val.startswith('"') and raw_val.endswith('"'):
                actual = raw_val[1:-1]
            last_actual = actual

            if AssertionEngine.compare(actual, expected, operator):
                return {
                    'status': 'PASS',
                    'reason': f"JSON路径 [{path}] 校验成功 (尝试 {attempt} 次)：实际 '{actual}'"
                }

            elapsed = time.time() - start_time
            if elapsed >= timeout:
                break
            time.sleep(interval)

        return {'status': 'FAIL', 'reason': f"JSON断言超时：实际值为 '{last_actual}'"}