"""
Job相关动作（通用动作）

设计理念：
- 通用动作只负责Job的调度（提交到调度平台）
- Job执行完成的判断逻辑高度业务化，应由业务动作实现
- 不同Job的状态记录方式、成功标准、失败处理都不同，无法通用化
"""
from typing import Any, Dict
import time
import requests
from actions.action_registry import action_registry
from actions.base import ExecutionAction, ActionMetadata
from config.settings import settings


@action_registry.register_decorator()
class TriggerScheduledJobAction(ExecutionAction):
    """
    触发定时任务动作（通用版本）

    设计理念：
    - external_data参数完全由外部传入，不在动作中定义死
    - 支持任意格式的外部参数（dict、json string、或无参数）
    - 具备通用性，可适配不同的Job场景

    重要说明：
    - 此动作只负责调度Job（告诉调度平台启动Job）
    - Job是否真正执行，取决于业务系统的Job内部逻辑
    - 不同Job的执行状态记录方式不同：
      * AiScriptUidPullJob: 会在common_job_status表中记录
      * AiScriptCompensateJob: 不会在表中记录调度任务
    """

    metadata = ActionMetadata(
        name='trigger_scheduled_job',
        category='business',
        description='触发定时任务（调用公司统一的Job调度平台），支持灵活的外部参数',
        parameters=[
            {
                'name': 'app_name',
                'type': 'str',
                'required': True,
                'description': '应用名称'
            },
            {
                'name': 'job_name',
                'type': 'str',
                'required': True,
                'description': 'Job名称（如AiScriptUidPullJob）'
            },
            {
                'name': 'external_data',
                'type': 'str',
                'required': False,
                'description': 'Job外部参数（可选）。支持普通字符串或JSON字符串。示例: "{\\"source\\": \\"postLoan\\"}" 或 "batch_20260209"'
            },
            {
                'name': 'sharding_flag',
                'type': 'bool',
                'required': False,
                'description': '是否分片执行（默认False）'
            },
            {
                'name': 'sharding_total',
                'type': 'int',
                'required': False,
                'description': '分片总数（仅当sharding_flag=True时有效，默认0）'
            }
        ],
        returns={
            'status': 'SUCCESS/FAIL',
            'job_id': 'Job执行ID',
            'message': '执行结果说明'
        }
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        """
        执行触发Job（调用公司统一的Job调度平台）

        Args:
            context: 执行上下文
            **params: 参数
                - job_name: Job名称
                - external_data: 外部参数（可选，dict格式）
                - sharding_flag: 是否分片（可选，bool）
                - sharding_total: 分片总数（可选，int）

        Returns:
            Dict: 执行结果
                - status: SUCCESS/FAIL
                - job_id: Job执行ID
                - message: 执行结果说明
        """
        self.validate_parameters(params)

        app_name = params['app_name']
        job_name = params['job_name']
        external_data = params.get('external_data', '')  # 默认为空字典
        sharding_flag = params.get('sharding_flag', False)  # 默认不分片
        sharding_total = params.get('sharding_total', 0)  # 默认分片数为0

        # 调用公司统一的Job调度平台
        try:
            result = self._trigger_job(app_name, job_name, external_data, sharding_flag, sharding_total)

            # 保存到上下文（包含source字段，用于后续状态查询）
            context.set('job_start_time',time.time())

            # context.set(f'{app_name}_{job_name}', {
            #     'external_data': external_data,
            #     'source': external_data.get('source', ''),  # 保存source字段
            #     'status': 'TRIGGERED',  # 状态改为TRIGGERED，表示已调度但未确认执行
            #     'start_time': time.time(),
            #     'flow_id': result.get('flow_id')
            # })

            return {
                'app_name': app_name,
                'job_name': job_name,
                'status': 'SUCCESS',
                'flow_id': result.get('flow_id'),
                'message': f'Job {job_name} 调度成功（已提交到调度平台）'
            }
        except Exception as e:
            return {
                'status': 'FAIL',
                'message': f'Job触发失败: {str(e)}'
            }

    def _trigger_job(self, app_name: str, job_name: str, external_data: str,
                     sharding_flag: bool = False, sharding_total: int = 0) -> Dict[str, Any]:
        """
        调用schedulerplus应用JOB启动接口（公司统一的Job调度函数）

        重要说明：
        - 此函数只负责调度Job（告诉调度平台启动Job）
        - Job是否真正执行，取决于业务系统的Job内部逻辑
        - 返回成功只表示调度请求已提交，不代表Job已执行

        Args:
            app_name: 应用名称
            job_name: Job名称
            external_data: 外部参数（字符串，可为空）
            sharding_flag: 是否分片执行
            sharding_total: 分片总数

        Returns:
            Dict: 响应结果
        """
        # 获取配置
        scheduler_url = settings.get('job.scheduler_url')
        uid = settings.get('job.default_uid')

        # 参数处理（按照公司标准函数的逻辑）
        import json

        # 处理sharding_flag
        if isinstance(sharding_flag, str):
            sharding_flag = True if sharding_flag.lower() == 'true' else False

        # 处理sharding_total
        if sharding_flag:
            if isinstance(sharding_total, str):
                sharding_total = int(sharding_total)
        else:
            sharding_total = 0

        # 调用API（按照公司标准函数的格式）
        url = f'{scheduler_url}/schedulerplus/job/flow/addFlow?p_u={uid}'
        data = {
            'jobGroup': app_name,
            'jobName': job_name,
            'executeType': 0,
            'shardingFlag': sharding_flag,
            'shardingTotal': sharding_total,
            'externalData': external_data,
            'remark': '默认（开发、测试环境自动填入）',
            'dataSize': '<10w',
            'dataRate': '<5kb/s',
            'tester': uid,
            'checkerOrg': '05523f37-4d0c-4084-86ee-fc0c559956de',
            'checker': '刘芳',
            'jiraNo': 'REQ-123',
            'jiraName': 'REQ-123'
        }

        print(f"    🚀 调度Job: {app_name}.{job_name}")
        print(f"       外部参数: {external_data}")
        if sharding_flag:
            print(f"       分片执行: {sharding_total} 个分片")

        # 添加详细日志
        print(f"    📡 调用URL: {url}")
        print(f"    📦 请求数据: {data}")

        response = requests.post(url=url, json=data, timeout=30)

        # 添加响应日志
        print(f"    📥 响应状态码: {response.status_code}")
        print(f"    📥 响应内容: {response.text[:500]}")  # 只打印前500字符

        if response.status_code != 200:
            raise ValueError(f'Job调度失败: HTTP {response.status_code}, {response.text}')

        result = response.json()
        print(f"    📊 解析后的响应: {result}")

        # 检查响应结果
        # 注意：调度平台有两种响应格式
        # 格式1（标准格式）: {"code": 200, "message": "成功", "data": {...}}
        # 格式2（直接返回）: {"flowNo": "AUTO-xxx", "orderSeq": xxx, "autoComplete": true, ...}

        if 'code' in result:
            # 格式1：标准格式，检查code字段
            if result.get('code') != 200:
                error_msg = result.get('message') or result.get('msg') or '未知错误'
                print(f"    ❌ 调度平台返回错误: code={result.get('code')}, message={error_msg}")
                print(f"    📋 完整响应: {result}")
                raise ValueError(f'Job调度失败: {error_msg}')
            print(f"    ✅ 调度成功（标准格式），返回数据: {result.get('data')}")
            return result.get('data', {})
        elif 'flowNo' in result:
            # 格式2：直接返回flowNo，说明调度成功
            print(f"    ✅ 调度成功（直接格式），flowNo={result.get('flowNo')}, orderSeq={result.get('orderSeq')}")
            return {
                'flow_id': result.get('flowNo'),
                'order_seq': result.get('orderSeq'),
                'auto_complete': result.get('autoComplete'),
                'bpm_link': result.get('bpmLink')
            }
        else:
            # 未知格式
            print(f"    ⚠️  未知的响应格式: {result}")
            raise ValueError(f'Job调度失败: 未知的响应格式')
