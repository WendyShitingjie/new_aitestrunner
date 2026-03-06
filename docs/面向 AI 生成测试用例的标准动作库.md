# 面向 AI 生成测试用例的标准动作库 (Standard Action Library)

## 1. 文档说明
本库定义了自动化测试框架中可用的**动作 (Actions)**。AI 在生成测试用例（YAML 格式）时，应严格遵守各动作的参数要求。

### 设计原则
- **职责分离**：执行类动作负责操作，断言类动作负责验证。
- **轮询支持**：数据库断言支持 `timeout` 参数，用于处理异步处理场景。
- **上下文关联**：接口调用结果默认存储在 `${http_response}`，后续断言通过 `path` 提取。

---

## 2. 数据操作类 (Database Actions)

### 2.1 database_insert
- **用途**：向数据库表中插入一条或多条测试数据，用于数据铺底。
- **参数**：
  - `database` (str): 数据库名。
  - `table` (str): 表名。
  - `data` (dict/list): 插入的数据。单条传 dict，多条传 list。
- **示例（插入单条）**：
```yaml
action: database_insert
params:
  database: "copilot"
  table: "ai_execute_config"
  data:
    code: "AI_CONFIG_001"
    name: "测试配置"
    source: "autotest"
```
- **示例（插入多条）**：
```yaml
action: database_insert
params:
  database: "copilot"
  table: "ai_execute_config"
  data:
    - code: "AI_CONFIG_001"
      name: "测试配置"
      source: "autotest"
    - code: "AI_CONFIG_002"
      name: "测试配置"
      source: "autotest"
```

### 2.2 database_delete
- **用途**：根据条件删除数据，常用于前置清理或后置环境还原。
- **参数**：
  - `database` (str): 数据库名。
  - `table` (str/list): 表名。支持单表字符串或多表列表。
  - `where` (str): SQL WHERE 子句（不含 WHERE 关键字）。
- **示例**：
```yaml
action: database_delete
params:
  database: "copilot"
  table: 
    - "ai_script_recommendation"
    - "ai_script_recommendation_log"
  where: "source='autotest' AND uid='user_001'"
```

### 2.3 database_update
- **用途**：更新数据库中的现有记录。
- **参数**：
  - `database` (str): 数据库名。
  - `table` (str): 表名。
  - `data` (dict): 要更新的字段及新值。
  - `where` (str): 更新条件。
- **示例**：
```yaml
action: database_update
params:
  database: "copilot"
  table: "ai_script_recommendation_log"
  data: 
    "execute_status": "SUCCESS"
  where: "serial_id='SN12345'"
```

---

## 3. 接口调用类 (API Actions)

### 3.1 call_http_api
- **用途**：发起 HTTP/HTTPS 请求。
- **参数**：
  - `application` (str): 应用名称（对应配置中的 base_url）。
  - `endpoint` (str): 接口路径。
  - `method` (str): 请求方法 (GET/POST/PUT/DELETE)。
  - `headers` (dict): 请求头。
  - `body` (dict/str): 请求体。
  - `timeout` (int): 超时时间（秒）。
- **示例**：
```yaml
action: call_http_api
params:
  application: "copilot"
  endpoint: "/ai/script/generate"
  method: POST
  body:
    uid: "user_001"
    serialId: "SN_001"
```

---

## 4. 校验断言类 (Assertion Actions)

### 4.1 assert_api_response
- **用途**：验证 API 返回的响应内容。
- **参数**：
  - `path` (str): 提取路径，如 `status_code`, `body.data.id`, `headers.Content-Type`。
  - `expected` (any): 期望值。
  - `operator` (str): 比较符。支持：`等于` (eq), `包含`, `不为空` (not_null), `is_numeric` 等。
- **示例**：
```yaml
action: assert_api_response
params:
  path: "body.generateStatus"
  operator: "等于"
  expected: "PROCESSING"
```

### 4.2 assert_database_field
- **用途**：断言数据库中指定记录的字段值。**支持超时轮询**。
- **参数**：
  - `database`, `table`, `field`, `where`: 查询定位参数。
  - `expected` (any): 期望值。
  - `timeout` (int): 最大等待时间（秒），用于异步链路验证。
  - `interval` (int): 轮询间隔，默认 2 秒。
- **示例**：
```yaml
action: assert_database_field
params:
  database: "copilot"
  table: "ai_script_recommendation_log"
  field: "execute_status"
  where: "serial_id='SN_001'"
  expected: "SUCCESS"
  timeout: 30
```

### 4.3 assert_database_json_field
- **用途**：专门用于断言数据库中 JSON 类型列内部的某个路径。
- **参数**：
  - `field` (str): JSON 列名。
  - `path` (str): JSON 路径（如 `$.data.name`）。
  - `expected`, `timeout` 等同上。
- **示例**：
```yaml
action: assert_database_json_field
params:
  database: "copilot"
  table: "ai_script_recommendation_log"
  field: "input_data"
  path: "$.contents"
  where: "serial_id='SN_001'"
  expected: "测试内容"
```

### 4.4 assert_value
- **用途**：通用值比较，不依赖具体媒介（如变量间比较）。
- **参数**：
  - `actual` (any): 实际值。
  - `expected` (any): 期望值。
  - `message` (str): 断言描述。
- **示例**：
```yaml
action: assert_value
params:
  actual: "${my_var}"
  expected: 100
  message: "验证变量值"
```

---

## 5. 任务调度类 (Job Actions)

### 5.1 trigger_scheduled_job
- **用途**：手动触发一个后端定时任务（Job）。
- **参数**：
  - `app_name` (str): 应用名。
  - `job_name` (str): Job 类名。
  - `external_data` (str): 传递给 Job 的参数字符串（通常为 JSON 格式）。
  - `sharding_flag` (bool): 是否分片执行（默认False）。
  - `sharding_total` (int): 分片总数（仅当sharding_flag=True时有效，默认0）。
- **示例**：
```yaml
action: trigger_scheduled_job
params:
  app_name: "copilot-job"
  job_name: "AiScriptCompensateJob"
  external_data: '{"source":"autotest"}'
```

---

## 6. YAML 用例结构规范 (Example Structure)

AI 生成用例时应采用以下层级结构：

```yaml
test_case_id: TC_XXX
test_name: "描述"
preconditions:
  - intent: "前置条件描述"
    action: <动作名称>
    params: 
      <参数1>: <参数1值>
      <参数2>: <参数2值>

test_steps:
  - intent: "步骤描述"
    action: call_http_api
    params: 
      <参数1>: <参数1值>
      <参数2>: <参数2值>      
    assertions: # 在步骤下直接挂载断言
      - intent: "断言描述1"
        action: <动作名称>
        params: 
          <参数1>: <参数1值>
          <参数2>: <参数2值>          
      - intent: "断言描述2"
        action: <动作名称>
        params: 
          <参数1>: <参数1值> 
          <参数2>: <参数2值>
```

### 比较符参考 (Operators)
- `等于` / `eq` / `==` / `=`
- `不等于` / `ne` / `!=` / `<>`
- `大于` / `gt` / `>`
- `小于` / `lt` / `<`
- `大于等于` / `ge` / `>=`
- `小于等于` / `le` / `<=`
- `包含` / `contains` / `in`
- `不包含` / `not_contains` / `not_in`
- `开头是` / `startswith`
- `结尾是` / `endswith`
- `正则` / `regex`
- `为空` / `is_null` / `null`
- `不为空` / `is_not_null` / `not_null`
- `是数字` / `is_numeric` / `numeric` / `number` (数值类型校验)