"""HTTP API调用动作（通用动作）

设计理念：
- 提供通用的HTTP/HTTPS接口调用能力
- 支持常见的HTTP方法（GET、POST、PUT、DELETE等）
- 支持请求头、请求体、查询参数等配置
- 自动保存响应到上下文，供后续断言使用
- 支持超时、重试等机制
"""
from typing import Any, Dict, Optional

import requests
import json
from actions.action_registry import action_registry
from actions.base import ExecutionAction, ActionMetadata
from config.settings import settings


@action_registry.register_decorator()
class CallHttpApiAction(ExecutionAction):
    """
    HTTP API调用动作（通用版本）

    设计理念：
    - 支持任意HTTP接口调用
    - 自动处理请求头、请求体的序列化
    - 自动保存响应到上下文
    - 支持变量替换（从上下文获取参数）

    重要说明：
    - 此动作只负责发送HTTP请求并获取响应
    - 响应的断言验证需要使用断言动作（assert_equals、assert_field_equals等）
    - 响应内容自动保存到上下文变量 ${http_response}
    """

    metadata = ActionMetadata(
        name='call_http_api',
        category='api',
        description='调用HTTP/HTTPS接口（支持GET、POST、PUT、DELETE等方法）',
        parameters=[
            {
                'name': 'application',
                'type': 'str',
                'required': True,
                'description': '应用名称，从配置文件读取base_url'
            },
            {
                'name': 'url',
                'type': 'str',
                'required': False,
                'description': '完整URL（如http://api.example.com/users）。优先使用此参数，如不传则使用base_url+endpoint'
            },
            {
                'name': 'endpoint',
                'type': 'str',
                'required': False,
                'description': '接口路径（如/users/123）。与base_url组合使用'
            },
            {
                'name': 'method',
                'type': 'str',
                'required': True,
                'description': 'HTTP方法（GET/POST/PUT/DELETE/PATCH）'
            },
            {
                'name': 'headers',
                'type': 'dict',
                'required': False,
                'description': '请求头（如{"Content-Type": "application/json"}）'
            },
            {
                'name': 'query_params',
                'type': 'dict',
                'required': False,
                'description': 'URL查询参数（如{"page": 1, "size": 10}）'
            },
            {
                'name': 'body',
                'type': 'dict/str',
                'required': False,
                'description': '请求体（dict会自动转JSON，str直接发送）'
            },
            {
                'name': 'timeout',
                'type': 'int',
                'required': False,
                'description': '超时时间（秒），默认10秒'
            },
            {
                'name': 'save_to_context',
                'type': 'str',
                'required': False,
                'description': '保存响应到上下文的变量名，默认为"http_response"'
            },
            {
                'name': 'verify_ssl',
                'type': 'bool',
                'required': False,
                'description': '是否验证SSL证书，默认True'
            }
        ],
        returns={
            'status': 'SUCCESS/FAIL',
            'status_code': 'HTTP状态码',
            'response_body': '响应体',
            'response_headers': '响应头',
            'message': '执行结果说明'
        }
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        """
        执行HTTP API调用

        Args:
            context: 执行上下文
            **params: 参数
                - application: 应用名称，从配置文件读取base_url
                - url: 完整URL（可选）
                - endpoint: 接口路径（可选）
                - method: HTTP方法
                - headers: 请求头（可选）
                - query_params: 查询参数（可选）
                - body: 请求体（可选）
                - timeout: 超时时间（可选，默认10秒）
                - save_to_context: 保存响应的变量名（可选，默认http_response）
                - verify_ssl: 是否验证SSL（可选，默认True）

        Returns:
            Dict: 执行结果
                - status: SUCCESS/FAIL
                - status_code: HTTP状态码
                - response_body: 响应体
                - response_headers: 响应头
                - message: 执行结果说明
        """
        self.validate_parameters(params)

        application = params['application']
        endpoint = params.get('endpoint', '').lstrip('/')
        method = params['method'].upper()
        timeout = params.get('timeout', 10)
        save_to_context_key = params.get('save_to_context', 'http_response')
        verify_ssl = params.get('verify_ssl', True)

        # 构建完整URL
        url = params.get('url')
        if not url:
            config = settings.http_api.get(application)
            if not config:
                return {
                    'status': 'FAIL',
                    'message': f"http_api配置不存在: {application}"
                }
            base_url = config.get('base_url')
            if not base_url:
                return {
                    'status': 'FAIL',
                    'message': f"base_url配置不存在: {application}"
                }
            url = f"{base_url}/{endpoint}" if endpoint else base_url

        # 构建请求头
        headers = params.get('headers', {})
        if 'Content-Type' not in headers and method in ['POST', 'PUT', 'PATCH']:
            headers['Content-Type'] = 'application/json'

        # 构建请求体
        body = params.get('body')
        if body and isinstance(body, dict) and headers.get('Content-Type') == 'application/json':
            body = json.dumps(body, ensure_ascii=False)

        # 构建查询参数
        query_params = params.get('query_params')

        # 发送HTTP请求
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=query_params,
                data=body,
                timeout=timeout,
                verify=verify_ssl
            )


            # 解析响应体
            response_body = None
            try:
                response_body = response.json()
            except json.JSONDecodeError:
                response_body = response.text


            # 构建结果
            result = {
                'status': 'SUCCESS',
                'status_code': response.status_code,
                'response_body': response_body,
                'response_headers': dict(response.headers),
                'message': f'HTTP请求成功: {method} {url} -> {response.status_code}'
            }

            # 保存响应到上下文
            context.set(save_to_context_key, {
                'status_code': response.status_code,
                'body': response_body,
                'headers': dict(response.headers)
            })

            return result

        except requests.exceptions.Timeout:
            return {
                'status': 'FAIL',
                'status_code': None,
                'response_body': None,
                'response_headers': None,
                'message': f'HTTP请求超时: {method} {url} (timeout={timeout}s)'
            }

        except requests.exceptions.ConnectionError as e:
            return {
                'status': 'FAIL',
                'status_code': None,
                'response_body': None,
                'response_headers': None,
                'message': f'HTTP请求连接失败: {method} {url} - {str(e)}'
            }

        except Exception as e:
            return {
                'status': 'FAIL',
                'status_code': None,
                'response_body': None,
                'response_headers': None,
                'message': f'HTTP请求异常: {method} {url} - {str(e)}'
            }