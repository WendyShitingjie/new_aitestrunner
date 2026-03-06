# AI 测试运行器 (AI Test Runner)

AI驱动的自动化测试框架，支持通过自然语言描述生成和执行测试用例。

## 概述

AI Test Runner是一个现代化的测试框架，它结合了人工智能技术和传统测试执行，允许用户通过自然语言意图描述测试用例，并能自动执行各种类型的测试，包括API测试、数据库测试、业务流程测试等。

## 核心特性

- **AI驱动测试生成**: 通过自然语言描述生成测试用例
- **多协议支持**: 支持HTTP API、数据库操作等多种测试类型
- **模块化架构**: 采用动作(Action)注册模式，易于扩展
- **上下文管理**: 自动管理测试执行过程中的数据流转
- **灵活的断言系统**: 支持多种断言操作符和复杂的校验逻辑
- **详细的报告**: 生成丰富的HTML测试报告
- **异步支持**: 支持异步操作验证（带轮询和超时机制）

## 项目结构

```
├── actions/                 # 测试动作实现
│   ├── base.py              # 动作基类
│   ├── action_registry.py   # 动作注册表
│   ├── generic/             # 通用动作
│   │   ├── api_operation.py    # API操作
│   │   ├── api_assertion.py    # API断言
│   │   ├── database_operation.py # 数据库操作
│   │   └── database_assertion.py # 数据库断言
│   └── business/            # 业务特定动作
│       └── datahub/
├── core/                    # 核心框架
│   ├── executor.py          # 测试执行器
│   ├── context.py           # 执行上下文
│   ├── intent_parser.py     # 意图解析器
│   ├── param_resolver.py    # 参数解析器
│   └── html_reporter.py     # HTML报告生成器
├── config/                  # 配置文件
├── functions/               # 辅助函数
├── cases/                   # 测试用例
├── reports/                 # 测试报告
├── docs/                    # 文档
├── run_test.py              # 主执行脚本
└── requirements.txt         # 依赖库
```

## 核心概念

### 1. 测试用例结构

AI Test Runner使用YAML格式定义测试用例，主要包括：

- `test_case_id`: 测试用例ID
- `test_name`: 测试用例名称
- `preconditions`: 前置条件（用于准备测试数据）
- `test_steps`: 测试步骤（执行主要测试逻辑）
- `assertions`: 断言（验证测试结果）

### 2. 动作系统 (Actions)

框架的核心是动作系统，包括：

- **操作类动作**: `database_insert`, `database_delete`, `call_http_api`
- **断言类动作**: `assert_api_response`, `assert_database_field`, `assert_value`
- **业务类动作**: 针对特定业务场景的自定义动作

### 3. 执行流程

1. **解析阶段**: 解析YAML测试用例，提取意图
2. **前置条件执行**: 执行所有预设条件，准备测试数据
3. **测试步骤执行**: 执行主要测试逻辑
4. **断言验证**: 验证执行结果是否符合预期
5. **报告生成**: 生成详细测试报告

## 配置说明

### 主要配置文件

`config/config.yaml` 包含以下配置：

- **数据库配置**: MySQL数据库连接信息
- **API配置**: HTTP服务基础URL
- **AI服务配置**: AI模型相关设置
- **执行配置**: 并发数、超时时间等执行参数
- **报告配置**: 报告输出路径和格式

### 支持的应用程序

配置中定义了多个应用程序的基础URL：

- `copilot`: 主要业务系统
- `scheduler`: 调度系统
- `ares`: 业务系统
- `aresplus`: 扩展业务系统

## 安装和使用

### 依赖安装

```bash
pip install -r requirements.txt
```

### 运行单个测试用例

```bash
python run_test.py cases/TC_TKI005_001_AI剧本信息实时生成_正常流程.yaml
```

### 批量运行测试用例

```bash
python run_test.py cases/
```

这将运行`cases`目录下的所有YAML文件，并生成批量测试报告。

## 示例测试用例

```yaml
test_case_id: TC_TKI005_001
test_name: AI剧本信息实时生成_正常流程
business_flow: TKI_005
priority: P0

test_intent:
  preconditions:
    - intent: "清空剧本推荐相关表的历史数据，确保测试环境干净"
      action: database_delete
      params:
        database: "copilot"
        table: "ai_script_recommendation_log"
        where: "source='autotest'"

  test_steps:
    - intent: "调用AI剧本信息实时生成接口"
      action: call_http_api
      params:
        application: "copilot"
        endpoint: "/copilot/ai/script/generate"
        method: POST
        body:
          serialId: "${uuid()}"
          uid: "${context.uid}"
          source: "autotest"
      assertions:
        - intent: "验证HTTP状态码为200"
          action: assert_api_response
          params:
            path: "status_code"
            expected: 200
```

## 动作库参考

### 数据库操作类

- `database_insert`: 插入数据
- `database_delete`: 删除数据
- `database_update`: 更新数据

### API操作类

- `call_http_api`: 调用HTTP接口

### 断言类

- `assert_api_response`: 验证API响应
- `assert_database_field`: 验证数据库字段值
- `assert_database_json_field`: 验证数据库JSON字段内部值
- `assert_value`: 通用值比较

## 高级特性

### 变量和函数支持

测试用例支持变量引用和内置函数：

- `${context.variable}`: 引用执行上下文中的变量
- `${uuid()}`: 生成UUID
- 支持其他自定义函数

### 异步验证

对于异步操作，断言支持超时轮询机制：

```yaml
action: assert_database_field
params:
  database: "copilot"
  table: "ai_script_recommendation_log"
  field: "execute_status"
  where: "serial_id='SN_001'"
  expected: "SUCCESS"
  timeout: 30
  interval: 3
```

## 报告系统

框架提供两种报告形式：

1. **详细报告**: 每个测试用例生成单独的HTML报告
2. **汇总报告**: 批量执行时生成包含所有测试用例的汇总页面，显示整体通过率和统计信息

报告包括：
- 测试用例基本信息
- 执行时间线
- 详细执行步骤
- 断言结果
- 性能指标

## 扩展性

AI Test Runner具有良好的扩展性：

1. **添加新动作**: 使用装饰器模式，直接在动作类定义处使用`@action_registry.register_decorator()`，实现自动注册
2. **自定义意图解析**: 实现自己的意图解析器
3. **新的报告格式**: 扩展报告生成器以支持新格式
4. **参数处理器**: 添加自定义参数解析逻辑

### 动作装饰器注册示例

```python
from actions.action_registry import action_registry
from actions.base import ExecutionAction, ActionMetadata

@action_registry.register_decorator()
class CustomAction(ExecutionAction):
    metadata = ActionMetadata(
        name='custom_action',
        category='custom',
        description='自定义动作示例',
        parameters=[
            {
                'name': 'param1',
                'type': 'str',
                'required': True,
                'description': '参数1描述'
            }
        ],
        returns={
            'status': 'SUCCESS/FAIL',
            'message': '执行结果'
        }
    )

    def execute(self, context, **params) -> dict:
        # 执行逻辑
        return {'status': 'SUCCESS', 'message': '执行成功'}
```

通过装饰器模式，开发者可以更便捷地创建和注册新动作，所有动作现在都通过自动发现机制注册，无需手动编辑配置文件。

## 最佳实践

1. **前置条件设计**: 前置条件应该确保测试环境的一致性和隔离性
2. **断言策略**: 使用适当的断言类型和操作符，充分利用超时轮询机制
3. **数据管理**: 使用唯一标识符防止数据冲突
4. **上下文利用**: 充分利用上下文机制在不同步骤间传递数据

## 使用场景

- API接口功能测试
- 业务流程验证
- 数据库操作测试
- 微服务集成测试
- 异步处理验证
- AI服务集成测试