"""打印变量值到日志的动作"""
from typing import Any, Dict
import json
from actions.action_registry import action_registry
from actions.base import ExecutionAction, ActionMetadata


@action_registry.register_decorator()
class PrintAction(ExecutionAction):
    """打印变量值到日志"""

    metadata = ActionMetadata(
        name='print',
        category='utility',
        description='打印变量值到日志,用于调试和查看上下文变量。支持打印单个或多个变量,支持嵌套对象的格式化输出。',
        parameters=[
            {
                'name': 'message',
                'type': 'str',
                'required': False,
                'description': '日志消息前缀,默认"打印日志"'
            },
            {
                'name': 'data',
                'type': 'any',
                'required': False,
                'description': '''要打印的数据,支持多种类型:
- 字符串: 从上下文读取变量(支持嵌套路径如"http_response.status_code")
- 字典: 打印字典内容(值可使用${var}模板语法)
- 列表/其他: 直接打印
- 为空: 打印整个上下文快照'''
            },
            {
                'name': 'pretty',
                'type': 'bool',
                'required': False,
                'default': True,
                'description': '是否格式化输出(仅对dict/list有效)'
            }
        ],
        returns={
            'status': 'SUCCESS',
            'message': '打印成功',
            'printed_values': '打印的内容'
        },
        examples=[
            {
                'description': '打印单个上下文变量',
                'yaml': '''
- intent: "打印HTTP响应状态码"
  action: "print"
  params:
    message: "API响应状态"
    data: "http_response.status_code"
'''
            },
            {
                'description': '打印嵌套路径变量',
                'yaml': '''
- intent: "打印响应体中的业务码"
  action: "print"
  params:
    message: "业务码"
    data: "http_response.body.code"
'''
            },
            {
                'description': '打印多个变量(使用字典)',
                'yaml': '''
- intent: "打印测试数据"
  action: "print"
  params:
    message: "当前测试上下文"
    data:
      用户ID: "${user_id}"
      批次号: "${batch_no}"
      响应码: "${http_response.body.code}"
'''
            },
            {
                'description': '打印直接值',
                'yaml': '''
- intent: "打印调试信息"
  action: "print"
  params:
    message: "执行检查点"
    data:
      step: "step1"
      status: "running"
'''
            },
            {
                'description': '打印整个上下文',
                'yaml': '''
- intent: "打印上下文快照"
  action: "print"
  params:
    message: "当前上下文"
'''
            }
        ]
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        """
        执行打印操作

        Args:
            context: 执行上下文
            **params: 参数
                - message: 日志消息前缀
                - data: 要打印的数据
                - pretty: 是否格式化输出

        Returns:
            Dict: 执行结果
        """
        message = params.get('message', '打印日志')
        data = params.get('data')
        pretty = params.get('pretty', True)

        print("\n" + "="*60)
        print(f"📋 {message}")
        print("="*60)

        printed_values = {}

        # 根据 data 的类型智能处理
        if data is None:
            # 场景1: data 为空，打印整个上下文快照
            context_snapshot = context.snapshot()
            formatted_value = self._format_value(context_snapshot, pretty)
            print(f"  上下文快照: {formatted_value}")
            printed_values['context'] = context_snapshot

        elif isinstance(data, str):
            # 场景2: data 是字符串，从上下文读取变量（支持嵌套路径）
            var_value = context.get(data)
            formatted_value = self._format_value(var_value, pretty)
            print(f"  {data}: {formatted_value}")
            printed_values[data] = var_value

        elif isinstance(data, dict):
            # 场景3: data 是字典，打印字典内容
            # 字典的值可能包含模板语法 ${var}，需要解析
            for label, value in data.items():
                # 如果值是字符串且包含 ${...} 模板语法，从上下文读取
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    var_name = value[2:-1]  # 去掉 ${ 和 }
                    actual_value = context.get(var_name)
                    formatted_value = self._format_value(actual_value, pretty)
                    print(f"  {label}: {formatted_value}")
                    printed_values[label] = actual_value
                else:
                    # 直接打印值
                    formatted_value = self._format_value(value, pretty)
                    print(f"  {label}: {formatted_value}")
                    printed_values[label] = value

        else:
            # 场景4: 其他类型（列表、数字等），直接打印
            formatted_value = self._format_value(data, pretty)
            print(f"  值: {formatted_value}")
            printed_values['value'] = data

        print("="*60 + "\n")

        return {
            'status': 'SUCCESS',
            'message': f'{message} - 打印成功',
            'printed_values': printed_values
        }

    def _format_value(self, value: Any, pretty: bool = True) -> str:
        """
        格式化输出值

        Args:
            value: 要格式化的值
            pretty: 是否美化输出

        Returns:
            str: 格式化后的字符串
        """
        if value is None:
            return "None"

        # 对于字典和列表,使用JSON格式化
        if isinstance(value, (dict, list)):
            if pretty:
                try:
                    return "\n" + json.dumps(value, ensure_ascii=False, indent=2)
                except Exception:
                    return str(value)
            else:
                try:
                    return json.dumps(value, ensure_ascii=False)
                except Exception:
                    return str(value)

        # 其他类型直接转字符串
        return str(value)
