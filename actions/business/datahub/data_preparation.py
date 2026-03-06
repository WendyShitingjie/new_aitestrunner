"""DataHub数据准备动作（业务动作）"""
import time
import random
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List
from actions.action_registry import action_registry
from actions.base import ExecutionAction, ActionMetadata
from utils.database import DatabaseConnection, parse_table_name


@action_registry.register_decorator()
class CreateOverdueUserAction(ExecutionAction):
    """创建逾期用户动作"""

    metadata = ActionMetadata(
        name='create_overdue_user',
        category='business',
        description='创建一个有逾期案件的用户',
        parameters=[
            {
                'name': 'overdue_days',
                'type': 'int',
                'required': True,
                'description': '逾期天数'
            },
            {
                'name': 'user_id',
                'type': 'str',
                'required': False,
                'description': '用户ID（不传则自动生成）'
            },
            {
                'name': 'loan_history',
                'type': 'int',
                'required': False,
                'default': 1,
                'description': '历史借款次数'
            },
            {
                'name': 'repay_history',
                'type': 'int',
                'required': False,
                'default': 0,
                'description': '历史还款次数'
            }
        ],
        returns={
            'user': '用户对象',
            'case': '案件对象'
        },
        examples=[
            {
                'description': '创建逾期15天、有还款记录的用户',
                'code': 'create_overdue_user(overdue_days=15, repay_history=2)'
            }
        ],
        related_business_rules=['BR_001'],
        related_data_models=['DM_001', 'DM_002']
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        """执行动作"""
        self.validate_parameters(params)

        # 1. 参数处理
        user_id = params.get('user_id') or self._generate_user_id()
        overdue_days = params['overdue_days']
        loan_history = params.get('loan_history', 1)
        repay_history = params.get('repay_history', 0)

        # 2. 生成用户数据
        user_data = {
            'user_id': user_id,
            'name': self._generate_name(),
            'phone': self._generate_phone(),
            'age': random.randint(20, 50),
            'gender': random.choice(['M', 'F']),
            'education': random.choice(['高中', '大专', '本科']),
            'occupation': random.choice(['私企职员', '个体户', '自由职业']),
            'create_time': datetime.now() - timedelta(days=overdue_days + 30),
            'overdue_days': overdue_days,
            'loan_history': loan_history,
            'repay_history': repay_history
        }

        # 3. 生成案件数据
        case_data = {
            'case_id': self._generate_case_id(),
            'user_id': user_id,
            'case_type': 'OVERDUE',
            'overdue_days': overdue_days,
            'overdue_amount': random.randint(1000, 10000),
            'status': 'ACTIVE',
            'create_time': datetime.now() - timedelta(days=overdue_days)
        }

        # 4. 存入上下文
        context.set('current_user', user_data, {
            'source': 'create_overdue_user',
            'overdue_days': overdue_days
        })
        context.set('current_case', case_data, {
            'source': 'create_overdue_user'
        })

        # 5. 返回结果
        return {
            'user': user_data,
            'case': case_data
        }

    def _generate_user_id(self) -> str:
        """生成用户ID"""
        return f"user_{int(time.time() * 1000)}"

    def _generate_case_id(self) -> str:
        """生成案件ID"""
        return f"case_{int(time.time() * 1000)}"

    def _generate_name(self) -> str:
        """生成随机姓名"""
        surnames = ['张', '王', '李', '赵', '刘', '陈', '杨', '黄']
        names = ['伟', '芳', '娜', '秀英', '敏', '静', '丽', '强']
        return random.choice(surnames) + random.choice(names)

    def _generate_phone(self) -> str:
        """生成随机手机号"""
        return f"13{random.randint(100000000, 999999999)}"


@action_registry.register_decorator()
class PrepareDPDataAction(ExecutionAction):
    """准备DP数据动作"""

    metadata = ActionMetadata(
        name='prepare_dp_data',
        category='business',
        description='在DataHub中准备DP产出的数据',
        parameters=[
            {
                'name': 'user_id',
                'type': 'str',
                'required': False,
                'description': '用户ID（不传则使用上下文中的current_user）'
            },
            {
                'name': 'batch_no',
                'type': 'str',
                'required': False,
                'description': '批次号（不传则自动生成）'
            }
        ],
        returns={
            'batch_no': '批次号'
        },
        related_business_rules=['BR_001'],
        related_data_models=['DM_003']
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        """执行动作"""
        # 从上下文获取用户ID
        user_id = params.get('user_id') or context.get('current_user.user_id')
        if not user_id:
            raise ValueError("缺少user_id参数，且上下文中没有current_user")

        # 生成批次号
        batch_no = params.get('batch_no') or self._generate_batch_no()

        # 模拟准备DP数据
        dp_data = {
            'user_id': user_id,
            'batch_no': batch_no,
            'status': 'READY',
            'create_time': datetime.now()
        }

        # 存入上下文
        context.set('current_batch', batch_no)
        context.set('dp_data', dp_data)

        return {'batch_no': batch_no}

    def _generate_batch_no(self) -> str:
        """生成批次号"""
        return datetime.now().strftime('%Y%m%d') + '001'


@action_registry.register_decorator()
class PrepareDatahubDataAction(ExecutionAction):
    """准备DataHub数据动作"""

    metadata = ActionMetadata(
        name='prepare_datahub_data',
        category='data',
        description='在DataHub中准备测试数据',
        parameters=[
            {
                'name': 'batch_no',
                'type': 'str',
                'required': False,
                'description': '批次号（不传则自动生成yyyyMMdd001格式）'
            },
            {
                'name': 'source',
                'type': 'str',
                'required': True,
                'description': '业务来源（如postLoan）'
            },
            {
                'name': 'batch_status',
                'type': 'str',
                'required': False,
                'default': '1',
                'description': '批次状态（1表示数据已产出）'
            },
            {
                'name': 'users',
                'type': 'list',
                'required': True,
                'description': '用户数据列表'
            }
        ],
        returns={
            'batch_no': '批次号',
            'user_count': '用户数量'
        }
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        """执行准备DataHub数据"""
        self.validate_parameters(params)

        # 如果没有传batch_no，则自动生成（yyyyMMdd001格式）
        batch_no = params.get('batch_no') or self._generate_batch_no()
        source = params['source']
        batch_status = params.get('batch_status', '1')
        users = params['users']

        print(f"    📦 使用批次号: {batch_no}")

        # 0. 验证AI执行配置（如果用户数据中包含ai_execute_code）
        ai_execute_codes = set()
        for user in users:
            if user.get('ai_execute_code'):
                ai_execute_codes.add(user.get('ai_execute_code'))

        for code in ai_execute_codes:
            if not self._validate_ai_execute_config(source, code):
                print(f"    ⚠️  警告: AI执行配置不存在 (source={source}, code={code})")
                print(f"    💡 建议: 请先在 copilot.ai_execute_config 表中添加配置记录")

        # 1. 为没有UID的用户生成UUID
        generated_uids = []
        for user in users:
            if not user.get('uid'):
                user['uid'] = str(uuid.uuid4()).replace('-', '')
            generated_uids.append(user['uid'])

        # 2. 插入批次状态记录到 ads_app_collect_script_result_df
        self._insert_batch_status(batch_no, source, batch_status)

        # 3. 插入用户基础数据到 ads_app_collect_script_base_df
        self._insert_user_base_data(batch_no, source, users)

        # 4. 插入用户扩展数据到 ads_app_collect_script_ext_df
        self._insert_user_ext_data(batch_no, source, users)

        # 保存到上下文（供后续步骤使用）
        context.set('datahub_batch_no', batch_no)
        context.set('datahub_user_count', len(users))
        context.set('datahub_uids', generated_uids)  # 保存生成的uid列表
        context.set('batch_no', batch_no)  # 保存batch_no到上下文，供后续步骤使用
        context.set('uids', generated_uids)  # 简化访问路径

        return {
            'status': 'SUCCESS',
            'batch_no': batch_no,
            'user_count': len(users),
            'uids': generated_uids,  # 返回uid列表
            'message': f'成功准备 {len(users)} 个用户的DataHub数据'
        }

    def _generate_batch_no(self) -> str:
        """生成批次号（yyyyMMdd001格式）"""
        return datetime.now().strftime('%Y%m%d') + '001'

    def _validate_ai_execute_config(self, source: str, ai_execute_code: str) -> bool:
        """验证AI执行配置是否存在"""
        try:
            sql = """
                SELECT COUNT(*) as cnt
                FROM copilot.ai_execute_config
                WHERE source = %s AND code = %s
            """
            results = DatabaseConnection.execute_query('copilot', sql, (source, ai_execute_code))
            return results[0]['cnt'] > 0 if results else False
        except Exception as e:
            print(f"    ⚠️  验证AI执行配置失败: {e}")
            return False

    def _insert_batch_status(self, batch_no: str, source: str, batch_status: str):
        """插入批次状态记录 - 确保batch_no+source唯一性"""
        try:
            # 先删除已存在的记录，确保唯一性
            delete_sql = """
                DELETE FROM datahub.ads_app_collect_script_result_df
                WHERE batch_no = %s AND source = %s
            """
            DatabaseConnection.execute_update('datahub', delete_sql, (batch_no, source))

            # 插入新记录
            insert_sql = """
                INSERT INTO datahub.ads_app_collect_script_result_df
                (batch_no, source, batch_status)
                VALUES (%s, %s, %s)
            """
            DatabaseConnection.execute_update('datahub', insert_sql, (batch_no, source, batch_status))
        except Exception as e:
            print(f"    ⚠️  插入批次状态失败: {e}")
            # 继续执行，不中断测试

    def _insert_user_base_data(self, batch_no: str, source: str, users: List[Dict]):
        """插入用户基础数据"""
        for user in users:
            try:
                # 根据实际表结构，包含所有字段
                sql = """
                    INSERT INTO datahub.ads_app_collect_script_base_df
                    (batch_no, source, uid, customer_name, age, sex, degree, company_name,
                     ident_address, marital_status, income, ai_execute_code, queue_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    customer_name = VALUES(customer_name),
                    age = VALUES(age),
                    sex = VALUES(sex),
                    degree = VALUES(degree),
                    company_name = VALUES(company_name),
                    ident_address = VALUES(ident_address),
                    marital_status = VALUES(marital_status),
                    income = VALUES(income),
                    ai_execute_code = VALUES(ai_execute_code),
                    queue_name = VALUES(queue_name)
                """
                DatabaseConnection.execute_update('datahub', sql, (
                    batch_no,
                    source,
                    user.get('uid'),
                    user.get('customerName', ''),
                    user.get('age', ''),
                    user.get('sex', ''),
                    user.get('degree', ''),
                    user.get('companyName', ''),
                    user.get('identAddress', ''),
                    user.get('maritalStatus', ''),
                    user.get('income', ''),
                    user.get('ai_execute_code', ''),
                    user.get('queue_name', '')
                ))
            except Exception as e:
                print(f"    ⚠️  插入用户基础数据失败 (uid={user.get('uid')}): {e}")

    def _insert_user_ext_data(self, batch_no: str, source: str, users: List[Dict]):
        """插入用户扩展数据 - 使用field_key和field_value键值对结构（按标准顺序）"""
        for user in users:
            uid = user.get('uid')

            # 扩展字段列表（按业务标准顺序，共23个字段）
            ext_fields = [
                ('deviceModel', user.get('deviceModel', '')),
                ('complainCnt', user.get('complainCnt', '')),
                ('contactNameFst', user.get('contactNameFst', '')),
                ('contactRelationFst', user.get('contactRelationFst', '')),
                ('concatCnt', user.get('concatCnt', '')),
                ('overdueDays', user.get('overdueDays', '')),
                ('totalOverdueAmount', user.get('totalOverdueAmount', '')),
                ('totalOverduePrincipal', user.get('totalOverduePrincipal', '')),
                ('loanCnt', user.get('loanCnt', '')),
                ('bairongCode', user.get('bairongCode', '')),
                ('pudaoCode', user.get('pudaoCode', '')),
                ('overdueCnt', user.get('overdueCnt', '')),
                ('latestRepayTime', user.get('latestRepayTime', '')),
                ('ruleCode', user.get('ruleCode', '')),
                ('monthRepayAmount', user.get('monthRepayAmount', '')),
                ('latestOutcallStatus', user.get('latestOutcallStatus', '')),
                ('callAnswerRate', user.get('callAnswerRate', '')),
                ('callCnt', user.get('callCnt', '')),
                ('laterstAiCallSummary', user.get('laterstAiCallSummary', '')),
                ('laterstManualCallSummary', user.get('laterstManualCallSummary', '')),
                ('contents', user.get('contents', '')),
                ('isFirstOverdue', user.get('isFirstOverdue', '')),
                ('latestSixMonthOverdueCnt', user.get('latestSixMonthOverdueCnt', ''))
            ]

            # 为每个扩展字段插入一条记录（按顺序）
            for field_key, field_value in ext_fields:
                if field_value:  # 只插入有值的字段
                    try:
                        sql = """
                            INSERT INTO datahub.ads_app_collect_script_ext_df
                            (uid, source, field_key, field_value)
                            VALUES (%s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                            field_value = VALUES(field_value)
                        """
                        DatabaseConnection.execute_update('datahub', sql, (
                            uid,
                            source,
                            field_key,
                            str(field_value)
                        ))
                    except Exception as e:
                        print(f"    ⚠️  插入用户扩展数据失败 (uid={uid}, field={field_key}): {e}")


@action_registry.register_decorator()
class CleanTestDataAction(ExecutionAction):
    """清理测试数据动作"""

    metadata = ActionMetadata(
        name='clean_test_data',
        category='data',
        description='清理测试数据',
        parameters=[
            {
                'name': 'batch_no',
                'type': 'str',
                'required': False,
                'description': '批次号（不传则自动生成当天的批次号yyyyMMdd001）'
            },
            {
                'name': 'source',
                'type': 'str',
                'required': True,
                'description': '业务来源'
            },
            {
                'name': 'tables',
                'type': 'list',
                'required': True,
                'description': '要清理的表列表（格式：database.table）'
            }
        ],
        returns={
            'deleted_count': '删除的记录数'
        }
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        """执行清理测试数据"""
        self.validate_parameters(params)

        # 如果没有传batch_no，则自动生成当天的批次号
        batch_no = params.get('batch_no') or self._generate_batch_no()
        source = params['source']
        tables = params['tables']

        print(f"    🧹 清理批次号: {batch_no}")

        total_deleted = 0

        for full_table_name in tables:
            db_name, table_name = parse_table_name(full_table_name)

            try:
                # 根据实际表结构选择删除条件
                if 'common_job_status' in table_name:
                    # common_job_status表：有batch_no，没有source，有business_type
                    sql = f"DELETE FROM {db_name}.{table_name} WHERE batch_no = %s"
                    deleted = DatabaseConnection.execute_update(db_name, sql, (batch_no,))

                elif 'ai_script_recommendation_log' in table_name:
                    # ai_script_recommendation_log表：有source，没有batch_no
                    sql = f"DELETE FROM {db_name}.{table_name} WHERE source = %s"
                    deleted = DatabaseConnection.execute_update(db_name, sql, (source,))

                elif 'ai_script_recommendation' in table_name:
                    # ai_script_recommendation表：有source，没有batch_no
                    sql = f"DELETE FROM {db_name}.{table_name} WHERE source = %s"
                    deleted = DatabaseConnection.execute_update(db_name, sql, (source,))

                elif 'ads_app_collect_script_result_df' in table_name:
                    # DataHub批次状态表：有batch_no和source
                    sql = f"DELETE FROM {db_name}.{table_name} WHERE batch_no = %s AND source = %s"
                    deleted = DatabaseConnection.execute_update(db_name, sql, (batch_no, source))

                elif 'ads_app_collect_script_base_df' in table_name:
                    # DataHub用户基础表：有batch_no和source
                    sql = f"DELETE FROM {db_name}.{table_name} WHERE batch_no = %s AND source = %s"
                    deleted = DatabaseConnection.execute_update(db_name, sql, (batch_no, source))

                elif 'ads_app_collect_script_ext_df' in table_name:
                    # DataHub用户扩展表：有source，没有batch_no
                    sql = f"DELETE FROM {db_name}.{table_name} WHERE source = %s"
                    deleted = DatabaseConnection.execute_update(db_name, sql, (source,))

                else:
                    # 默认使用batch_no和source
                    sql = f"DELETE FROM {db_name}.{table_name} WHERE batch_no = %s AND source = %s"
                    deleted = DatabaseConnection.execute_update(db_name, sql, (batch_no, source))

                total_deleted += deleted
                print(f"    清理 {full_table_name}: {deleted} 条记录")

            except Exception as e:
                print(f"    ⚠️  清理 {full_table_name} 失败: {e}")

        return {
            'status': 'SUCCESS',
            'deleted_count': total_deleted,
            'message': f'成功清理 {total_deleted} 条测试数据'
        }

    def _generate_batch_no(self) -> str:
        """生成批次号（yyyyMMdd001格式）"""
        return datetime.now().strftime('%Y%m%d') + '001'