# AI Test Runner

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.0-orange.svg)](https://github.com)

**基于 AI 驱动的智能化测试用例生成与执行框架**

[快速开始](#-快速开始) • [使用文档](#-使用说明) • [架构设计](#-核心架构) • [贡献指南](#-贡献与开发)

</div>

---

## 📖 项目介绍

AI Test Runner 是一款**面向知识驱动的 AI 自动化测试框架**，专为复杂业务系统的端到端测试而设计。该框架解决了传统测试用例编写效率低、维护成本高、业务覆盖不全面等痛点。

### 核心能力

🎯 **AI 智能生成测试用例**
- 基于知识要素（YAML 格式），通过大语言模型（LLM）自动推理生成完整的 YAML 测试脚本
- 支持复杂业务规则解析、数据依赖推导、异步流程验证

🚀 **全链路测试执行**
- 支持数据库操作（增删改查、断言）、HTTP API 调用、定时任务触发
- 内置轮询机制，处理异步业务场景（如消息队列、后台任务）
- 自动化前置条件构造（数据清理、数据铺底）

📊 **丰富的测试报告**
- 生成精美的 HTML 测试报告，支持知识要素覆盖信息、依赖知识要素追踪
- 提供汇总报告和详细报告，快速定位失败原因
- 支持批量执行结果聚合展示

🏗️ **TDD 工作流支持**
- 按需求维度组织用例（`TDD/REQ-xxxxx/`）
- 自动管理用例批次（`case_{timestamp}`）和执行批次（`run_{timestamp}`）
- 支持知识库版本化管理

---

## 🛠 技术栈概览

### 核心技术

| 类别 | 技术选型 | 用途 |
|------|---------|------|
| **编程语言** | Python 3.8+ | 核心开发语言 |
| **LLM 集成** | OpenAI SDK | 支持 OpenAI、阿里云通义千问、字节豆包等 |
| **数据库驱动** | PyMySQL | MySQL 连接与操作 |
| **HTTP 客户端** | Requests | API 接口调用 |
| **配置管理** | PyYAML | 测试用例、配置文件解析 |
| **数据验证** | Pydantic | 参数校验与类型检查 |
| **日志系统** | Loguru | 结构化日志输出 |
| **测试框架** | Pytest | 单元测试（可选） |

### 架构特性

- **插件化设计**：动作（Actions）和函数（Functions）自动注册发现
- **上下文管理**：全局变量传递、动态数据生成、参数联动
- **模板引擎**：支持 `${变量名}` 和 `${函数()}` 表达式解析
- **异常处理**：完善的错误捕获、回滚机制、断言超时重试

---

## 📂 核心目录结构

```
aitestrunner/
├── actions/                   # 测试动作库（可扩展）
│   ├── base.py                # 动作基类
│   ├── action_registry.py     # 动作注册器
│   ├── generic/               # 通用动作
│   │   ├── database_operation.py   # 数据库操作（增删改查）
│   │   ├── database_assertion.py   # 数据库断言（字段值、记录数、JSON 路径）
│   │   ├── api_operation.py        # HTTP API 调用
│   │   ├── job_operation.py        # 定时任务触发
│   │   ├── noop.py                 # 空操作（占位/跳过）
│   │   └── print.py                # 日志打印
│   └── business/              # 业务专用动作（自定义扩展）
│
├── core/                      # 核心执行引擎
│   ├── executor.py            # 主执行器（TestCase → TestResult）
│   ├── context.py             # 执行上下文管理
│   ├── param_resolver.py      # 参数解析器（${} 表达式替换）
│   ├── intent_parser.py       # 意图解析器（可选 LLM 增强）
│   └── html_reporter.py       # HTML 报告生成器
│
├── functions/                 # 内置函数库（可扩展）
│   ├── function_registry.py   # 函数注册器
│   └── generic/
│       └── common_funcs.py    # 通用函数（uuid、timestamp、batch_no）
│
├── utils/                     # 工具类
│   ├── database.py            # 数据库连接池
│   └── assertion_engine.py    # 断言引擎（支持轮询、比较运算符）
│
├── config/                    # 配置管理
│   ├── config.yaml            # 全局配置（LLM、数据库、HTTP API）
│   ├── settings.py            # 配置加载器
│   └── knowledge_mapping.yaml # 业务知识映射（可选）
│
├── prompt/                    # LLM 提示词模板
│   ├── prompt.case_script_gen.system.md  # 系统提示词
│   └── prompt.case_script_gen.user.md    # 用户提示词模板
│
├── TDD/                       # 测试驱动开发工作区
│   └── REQ-xxxxx-需求名称/     # 按需求组织
│       ├── elements/          # 知识库（YAML）
│       │   ├── AI_*.yaml      # 接口类知识要素
│       │   ├── AD_*.yaml      # 数据类知识要素
│       │   └── AJ_*.yaml      # 任务类知识要素
│       ├── cases/             # 生成的测试用例
│       │   └── case_20260318_101112/  # 用例批次
│       │       ├── TC_*.yaml          # YAML 测试用例
│       │       ├── user_prompt.md     # 用户提示词（调试）
│       │       └── llm_response.md    # LLM 响应（调试）
│       └── reports/           # 测试报告
│           └── case_20260318_101112/  # 对应用例批次
│               └── run_20260318_143520/  # 执行批次
│                   ├── index.html        # 汇总报告
│                   └── TC_*.html         # 详细报告（一个用例一个）
│
├── docs/                      # 项目文档
│   └── 面向AI生成测试用例的测试知识库.md
│
├── case_gen_v2.py             # 用例生成器（LLM 驱动）
├── case_run_v2.py             # 用例执行器（支持单文件/目录）
├── requirements.txt           # Python 依赖清单
└── README.md                  # 本文档
```

---

## 🚀 快速开始

### 环境要求

- **Python**：3.8 或更高版本
- **数据库**：MySQL 5.7+ （如需执行数据库相关测试）
- **LLM API**：OpenAI API 兼容服务（如 OpenAI、阿里云通义千问、字节豆包）

### 安装步骤

#### 1. 克隆项目

```bash
git clone <repository_url>
cd aitestrunner
```

#### 2. 安装依赖

```bash
# 创建虚拟环境（推��）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

#### 3. 配置文件

编辑 `config/config.yaml`，配置以下必需项：

```yaml
# LLM 配置（用例生成）
llm:
  api_key: "your-api-key"              # 替换为你的 API Key
  base_url: "https://api.openai.com/v1"  # 或其他兼容服务
  model: "gpt-4"                       # 模型名称

# 数据库配置（根据实际测试环境）
database:
  your_db:
    host: "localhost"
    port: 3306
    user: "test_user"
    password: "test_password"
    database: "test_db"

# HTTP API 配置（根据被测系统）
http_api:
  your_service:
    base_url: "http://localhost:8080"
    timeout: 60
```

**⚠️ 安全提示**：敏感信息建议通过环境变量注入，避免提交到版本控制。

---

## 💡 使用说明

### 一、准备知识库

在 `TDD/REQ-xxxxx-需求名称/elements/` 目录下，创建知识要素定义文件（YAML 格式）。

**示例**：`AI_user_login.yaml`（接口类知识要素）

```yaml
type: AI-系统接口类知识要素
id: AI_user_login
name: 用户登录接口
version: v1.0
description: 用户通过账号密码登录系统

keys:
  type: API
  app: user_service
  method: POST
  endpoint: /api/v1/user/login

dependencies:
  - name: AD_user_table
    type: MySQL
    description: 用户表，存储账号、密码哈希

logic_rules:
  - rule: 账号密码校验
    description: |
      - 账号不存在：返回 404
      - 密码错误：返回 401
      - 验证成功：返回 200 + JWT Token

request:
  body:
    required: true
    schema:
      username:
        type: string
        required: true
      password:
        type: string
        required: true

response:
  status:
    200:
      description: 登录成功
      body:
        token: string
    401:
      description: 密���错误
    404:
      description: 账号不存在
```

### 二、生成测试用例

使用 `case_gen_v2.py` 自动生成测试用例：

```bash
# 仅生成 YAML 用例（不执行）
python case_gen_v2.py TDD/REQ-12345-用户登录/elements/AI_user_login.yaml

# 生成用例并立即执行
python case_gen_v2.py TDD/REQ-12345-用户登录/elements/AI_user_login.yaml --run
```

**输出示例**：

```
📂 需求目录: TDD/REQ-12345-用户登录
📁 用例批次目录: TDD/REQ-12345-用户登录/cases/case_20260318_143025
🤖 LLM 模型: gpt-4

📖 正在读取目标知识要素: AI_user_login.yaml
   知识要素编号: AI_user_login
   知识要素名称: 用户登录接口

📚 正在加载 1 个依赖知识要素:
   ✓ AD_user_table - 用户表

🔧 正在构��用户提示词...
   ✓ 用户提示词构建完成
   ✓ 用户提示词已保存: user_prompt.md

🤖 正在调用 LLM 生成测试用例...
======================================================================
<thinking>...</thinking>

```yaml
test_case_id: TC_AI_user_login_001
test_case_name: 用户登录_合法账号密码_登录成功
...
```
======================================================================
✓ LLM 响应完成

📝 正在解析并保存测试用例...
   ✓ 已保存: TC_AI_user_login_001.yaml - 用户登录_合法账号密码_登录成功
   ✓ 已保存: TC_AI_user_login_002.yaml - 用户登录_账号不存在_返回404
   ✓ 已保存: TC_AI_user_login_003.yaml - 用户登录_密码错误_返回401

✓ 共保存 3 个测试用例文件
```

### 三、执行测试用例

使用 `case_run_v2.py` 执行测试用例：

```bash
# 批量执行（目录下所有 YAML 文件）
python case_run_v2.py TDD/REQ-12345-用户登录/cases/case_20260318_143025

# 执行单个用例
python case_run_v2.py TDD/REQ-12345-用户登录/cases/case_20260318_143025/TC_AI_user_login_001.yaml
```

**输出示例**：

```
======================================================================
  AI 测试框架 V2 - 批量执行
======================================================================
📁 报告输出目录: TDD/REQ-12345-用户登录/reports/case_20260318_143025/run_20260318_150530
找到 3 个测试用例文件

初始化测试执行器...

======================================================================
开始执行测试用例...
======================================================================

[1/3] ============================================================
执行测试用例: TC_AI_user_login_001.yaml

============================================================
测试结果: PASS
执行时间: 2.34 秒
============================================================

[2/3] ============================================================
...

======================================================================
批量执行汇总
======================================================================
总用例数: 3
通过: 3
失败: 0
通过率: 100.0%
总耗时: 7.12 秒

汇总报告: TDD/REQ-12345-用户登录/reports/case_20260318_143025/run_20260318_150530/index.html
======================================================================
```

### 四、查看测试报告

在浏览器中打开汇总报告：

```
TDD/REQ-12345-用户登录/reports/case_20260318_143025/run_20260318_150530/index.html
```

报告包含：
- ✅ 执行统计（总数、通过、失败、通过率、耗时）
- 📋 用例列表（状态、用例 ID、名称、断言数）
- 🔗 详细报告链接（点击查看每个用例的执行细节）

详细报告（`TC_xxx.html`）包含：
- 🎯 知识要素覆盖信息（目标知识要素、依赖知识要素）
- 📊 执行统计（前置条件、测试步骤、断言结果）
- 🔍 详细执行日志（参数值、响应数据、断言过程）

---

## 🎓 核心架构

### 执行流程

```
┌───────────────┐
│ YAML 测试用例 │
└───────┬───────┘
        │
        ▼
┌───────────────────────────────────────────┐
│  AITestExecutor (core/executor.py)       │
│  ┌─────────────────────────────────────┐ │
│  │ 1. 解析 YAML                        │ │
│  │ 2. 初始化上下文 (ExecutionContext)  │ │
│  │ 3. 执行 preconditions               │ │
│  │ 4. 执行 test_steps                  │ │
│  │ 5. 断言验证 (assertions)            │ │
│  │ 6. 生成测试报告                     │ │
│  └─────────────────────────────────────┘ │
└───────────────┬───────────────────────────┘
                │
     ┌──────────┼──────────┐
     │          │          │
     ▼          ▼          ▼
┌─────────┐ ┌──────┐ ┌──────────┐
│ Actions │ │ Funcs│ │ Reporter │
│ Registry│ │ Reg. │ │  (HTML)  │
└─────────┘ └──────┘ └──────────┘
```

### 参数解析机制

**动态数据生成**：`${uuid()}` → 调用 `functions/generic/common_funcs.py`

**上下文变量引用**：`${context.user_id}` → 从 `ExecutionContext` 读取

**参数联动示例**：

```yaml
preconditions:
  - intent: "生成用户 ID"
    action: "print"
    params:
      data:
        user_id: "${uuid()}"  # ← 生成随机 UUID

test_steps:
  - intent: "调用登录接口"
    action: "call_http_api"
    params:
      endpoint: "/api/v1/user/login"
      body:
        user_id: "${context.data.user_id}"  # ← 引用上一步生成的 UUID
```

### 断言轮询机制

针对异步场景（如消息队列、后台任务），支持超时轮询：

```yaml
assertions:
  - intent: "异步校验订单状态更新"
    action: "assert_database_field"
    params:
      database: "order_db"
      table: "orders"
      field: "status"
      where: "order_id='${context.data.order_id}'"
      expected: "SUCCESS"
      timeout: 60      # 最多等待 60 秒
      interval: 2      # 每 2 秒轮询一次
```

---

## 🤝 贡献与开发

### 开发指南

#### 扩展自定义动作

1. 在 `actions/business/` 下创建 Python 文件
2. 继承 `actions/base.py` 中的 `BaseAction`
3. 实现 `execute()` 方法

**示例**：

```python
# actions/business/send_email.py
from actions.base import BaseAction

class SendEmailAction(BaseAction):
    """发送邮件动作"""

    def execute(self, **params):
        recipient = params['recipient']
        subject = params['subject']
        body = params['body']

        # 实现邮件发送逻辑
        # ...

        return {
            'status': 'SUCCESS',
            'message_id': 'msg-12345'
        }
```

动作会被自动发现并注册为 `send_email`（文件名）。

#### 扩展自定义函数

1. 在 `functions/generic/common_funcs.py` 中添加函数
2. 使用 `@register_function('函数名')` 装饰器

**示例**：

```python
from functions.function_registry import register_function
import hashlib

@register_function('md5')
def generate_md5(text: str) -> str:
    """生成 MD5 哈希"""
    return hashlib.md5(text.encode()).hexdigest()
```

在 YAML 中使用：`password_hash: "${md5('mypassword')}"`

### 代码规范

- **格式化**：使用 `black` 格式化代码
- **检查**：使用 `flake8` 检查代码风格
- **测试**：新增功能需补充单元测试（`pytest`）
- **文档**：更新对应的 Docstring 和 README.md

### 提交规范

```
<type>(<scope>): <subject>

示例：
feat(actions): 新增发送短信动作
fix(executor): 修复异步断言超时问题
docs(readme): 更新快速开始文档
```

---

## 📋 常见问题

**Q1：如何切换不同的 LLM 服务？**

A：修改 `config/config.yaml` 中的 `llm` 配置：

```yaml
llm:
  api_key: "your-key"
  base_url: "https://api.openai.com/v1"    # OpenAI
  # base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"  # 阿里云
  # base_url: "https://ark.cn-beijing.volces.com/api/v3"           # 字节豆包
  model: "gpt-4"
```

**Q2：生成的用例如何调试？**

A：查看 `cases/case_xxx/` 目录下的：
- `user_prompt.md`：发送给 LLM 的完整提示词
- `llm_response.md`：LLM 的原始响应内容

**Q3：如何处理敏感配置（如数据库密码）？**

A：建议使用环境变量：

```bash
export MYSQL_PASSWORD="your-password"
```

在 `config/settings.py` 中已支持环境变量覆盖（参见 `_override_from_env()` 方法）。

**Q4：支持哪些断言类型？**

A：参见 `docs/面向AI生成测试用例的测试知识库.md`，包括：
- `assert_value`：通用值比较
- `assert_database_field`：数据库字段断言（支持轮询）
- `assert_database_record_count`：记录数断言
- `assert_database_json_field`：JSON 字段路径断言
- 自定义断言（可扩展）

---

## 📄 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

感谢所有为本项目贡献代码、反馈问题、提出建议的开发者！

---

<div align="center">

**Made with ❤️ by AI Test Team**

[⬆️ 回到顶部](#ai-test-runner)

</div>
