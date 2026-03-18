# 面向AI生成测试用例的测试知识库

## 文档说明
本库定义了自动化测试框架中可用的**内置函数 (Functions)**、**动作 (Actions)**，以及上下文参数的引用说明。 AI 在生成测试用例脚本（YAML 格式）时，应严格遵守各函数、动作的参数要求。

### 设计原则
- **动态数据**：通过内置函数 `${函数名(参数)}`生成动态数据。
- **参数关联**：上下文参数引用 `${context.参数名}`。
- **职责分离**：执行类动作负责操作，断言类动作负责验证。
- **轮询支持**：数据库断言支持 `timeout` 参数，用于处理异步处理场景。
---

## 变量引用 (TV - Test Variable)
### ${context.变量名}
- **用途**：全文变量引用。
- **示例**：`${context.user_id}`

## 内置函数库 (TF - Test Function)
### uuid
- **用途**：生成随机 UUID。
- **调用语法**：`${uuid()}`
- **示例**：`id: "${uuid()}"`
### timestamp
- **用途**：获取当前时间戳。
- **调用语法**：`${timestamp()}`
- **示例**：`created_at: "${timestamp()}"`
### timestamp_minus_minutes
- **用途**：获取当前时间之前的分钟偏移时间。
- **参数**：`minutes` (Integer)。
- **调用语法**：`${timestamp_minus_minutes(n)}`
- **示例**：`created_at: "${timestamp_minus_minutes(10)}"`
### batch_no
- **用途**：生成批次号。
- **调用语法**：`${batch_no()}`

# 操作类动作 (TO - Test Operation)
### noop
- **用途**：空操作。
- **参数**：`reason` (str)。选填。跳过执行的原因说明
- **示例（临时跳过某个步骤）**：
```yaml
action: "noop"
params:
  reason: "开发中,暂不执行"
```
- **示例（占位步骤）**：
```yaml
action: "noop"
params: {}
```

### print
- **用途**：打印日志。
- **参数**：`message` (str)。选填。
- **参数**：`data` (any)。选填。要打印的数据（根据类型智能处理）。
- **参数**：`pretty` (boolean)。选填。是否格式化输出。默认为 true
- **示例（打印变量）**：
```yaml
action: "print"
params:
   data:
     用户ID: "${user_id}"
     状态码: "${http_response.status_code}"
```
- **示例（打印整个上下文快照）**：
```yaml
action: "print"
params:
  message: "当前上下文快照"
```

### database_insert
- **用途**：向数据库表中插入一条或多条测试数据，用于数据铺底。
- **参数**：
  - `database` (str): 必填。数据库名。
  - `table` (str): 必填。表名。
  - `data` (dict/list): 必填。插入的数据。单条传 dict，多条传 list。
- **示例（插入单条）**：
```yaml
action: database_insert
params:
  database: "copilot"
  table: "ai_execute_config"
  data:
    code: "AI_CONFIG_001"
    name: "测试配置"
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
    - code: "AI_CONFIG_002"
      name: "测试配置"
```
### database_delete
- **用途**：根据条件删除数据，常用于前置清理或后置环境还原。
- **参数**：
  - `database` (str): 必填。数据库名。
  - `table` (str/list): 必填。表名。支持单表字符串或多表列表。
  - `where` (str): SQL 必填。WHERE 子句（不含 WHERE 关键字）。
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
### database_update
- **用途**：更新数据库中的现有记录。
- **参数**：
  - `database` (str): 必填。数据库名。
  - `table` (str): 必填。表名。
  - `data` (dict): 必填。要更新的字段及新值。
  - `where` (str): 必填。更新条件。
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
### database_select
- **用途**：查询数据库中的数据。
- **参数**：
  - `database` (str): 必填。数据库名。
  - `table` (str/list): 必填。表名。支持单表字符串或多表列表。
  - `fields` (str/list): 选填。要查询的字段。默认为 "*"。
  - `where` (str): 选填。查询条件。
  - `order_by` (str): 选填。排序字段。
  - `limit` (int): 选填。限制条数。默认为 100。
- **示例**：
```yaml
action: database_select
params:
    database: "copilot"
    table: "ai_script_recommendation_log"
    fields: "*"
    where: "serial_id='SN12345'"
    order_by: "id DESC"
    limit: 100
```
### call_http_api
- **用途**：发起 HTTP/HTTPS 请求。
- **参数**：
  - `application` (str): 必填。应用名称（对应配置中的 base_url）。
  - `endpoint` (str): 必填。接口路径。
  - `method` (str): 必填。请求方法 (GET/POST/PUT/DELETE)。
  - `headers` (dict): 选填。查询参数。
  - `query_params` (dict): 选填。请求参数。
  - `body` (dict/str): 选填。请求体。
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
### trigger_scheduled_job
- **用途**：手动触发一个后端定时任务（Job）。
- **参数**：
  - `app_name` (str): 必填。应用名。
  - `job_name` (str): 必填。Job 类名。
  - `external_data` (str): 选填。传递给 Job 的参数字符串（通常为 JSON 格式）。
  - `sharding_flag` (bool): 选填。是否分片执行（默认False）。
  - `sharding_total` (int): 选填。分片总数（仅当sharding_flag=True时有效，默认0）。
- **示例**：
```yaml
action: trigger_scheduled_job
params:
  app_name: "copilot-job"
  job_name: "AiScriptCompensateJob"
  external_data: '{"source":"autotest"}'
```

# 断言类动作 (TA - Test Assertion)
### assert_value
- **用途**：通用值比较，不依赖具体媒介（如变量间比较）。
- **参数**：
  - `actual` (any): 实际值。必填。
  - `expected` (any): 期望值。为空判断时可不传填。
- **示例**：
```yaml
action: assert_value
params:
  actual: "${my_var}"
  expected: 100
```
### assert_database_field
- **用途**：断言数据库中指定记录的字段值。**支持超时轮询**。
- **参数**：
  - `database`, `table`, `field`, `where`: 查询定位参数。全部必填。
  - `expected` (any): 期望值。选填。
  - `operator` (str): 比较符。选填。默认为 "="。
  - `timeout` (int): 最大等待时间（秒），默认 10 秒。选填。
  - `interval` (int): 轮询间隔，默认 2 秒。选填。
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
### assert_database_record_count
- **用途**：断言符合条件的数据库记录行数是否达标（支持超时轮询）
- **参数**：
  - `database`, `table`, `where`: 必填。查询定位参数。
  - `operator` (str): 选填。比较符。选填。默认为 "="。
  - `expected` (any): 必填。期望值。
  - `timeout` (int): 选填。最大等待时间（秒），默认 10 秒。
  - `interval` (int): 选填。轮询间隔，默认 2 秒。

### assert_database_all_match
- **用途**：断言符合条件的数据库记录行数是否达标（支持超时轮询）
- **参数**：
  - `database`, `table`, `field`, `where`: 必填。查询定位参数。
  - `expected` (any): 必填。期望值。
  - `timeout` (int): 选填。最大等待时间（秒），默认 10 秒。
  - `interval` (int): 选填。轮询间隔，默认 2 秒。

### assert_database_json_field
- **用途**：专门用于断言数据库中 JSON 类型列内部的某个路径值是否满足条件（支持超时轮询）。
- **参数**：
- `database`, `table`, `field`, `where`: 必填。查询定位参数。
  - `field` (str): JSON 列名。
  - `path` (str): JSON 路径（如 `$.data.name`）。
  - `expected` (any): 必填。期望值。
  - `timeout` (int): 选填。最大等待时间（秒），默认 10 秒。
  - `interval` (int): 选填。轮询间隔，默认 2 秒。
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

### assert_api_response
- **用途**：验证 API 返回的响应内容。
- **参数说明**：
  - `path` (String): 必填。
  - `expected` (Any): 必填。期望值。
  - `operator` (String): 必填。比较方式。
    - 可选值：[等于, eq, 包含, contains, 不为空, not_null, regex, is_numeric]
- **示例**：
```yaml
action: assert_api_response
params:
  path: "body.code"
  operator: "等于"
  expected: 200
```