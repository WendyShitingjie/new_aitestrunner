# 用户提示词 (User Prompt)

## 1. 核心测试目标 (Core Test Target)
> **注意**：以下知识要素是本次测试的主体，所有测试步骤必须紧紧围绕该知识要素的逻辑展开。

### 目标知识要素

#### AI_copilot_ai_script_generate - AI剧本信息实时生成
```yaml
type: AI-系统接口类
code: AI_copilot_ai_script_generate
name: AI剧本信息实时生成
version: v2.0
description: 根据用户注记+特征配置调用AI平台生成个性化催收剧本，接口立即返回PROCESSING，后台异步完成。

# -------------------- 接口定义 --------------------
keys:
  type: API
  app: copilot
  method: POST
  endpoint: /copilot/ai/script/generate


# -------------------- 下游依赖知识要素 --------------------
dependencies:
  - code: AD_copilot_ai_script_recommendation_log
    type: MySQL
    description: 剧本推荐日志表，存储流水状态、input_data、AI返回结果output_data
    operations:
      - operation: read
        purpose: 幂等校验（查询serial_id是否存在）及获取基准数据（查询uid+source+updated_at最新记录）
        key_fields: [serial_id, uid, aiExecuteCode, source, updated_at]
      - operation: write
        purpose: 插入新流水（状态INIT）、中间状态（PROCESSING）及最终状态（SUCCESS/FAILURE）及结果
        key_fields: [serial_id, uid, queue, aiExecuteCode, triger_scene, source, execute_status, input_data, output_data, failure_reason]

  - code: AD_copilot_ai_execute_config
    type: MySQL
    description: AI执行配置表，存储AI配置信息
    operations:
      - operation: read
        purpose: 校验code=AD_copilot_ai_script_recommendation_log.aiExecuteCode是否存在
        key_fields: [ source, code, agent_workflow_code ]

  - code: AD_copilot_ai_script_recommendation
    type: MySQL
    description: 剧本推荐表，存储最终生成的剧本内容
    operations:
      - operation: write
        purpose: SUCCESS时Upsert最终剧本（基于uid+source）
        key_fields: [uid, source]

# -------------------- 核心业务规则 --------------------
logic_rules:
  - rule: 幂等处理
    description: |
      相同serial_id请求：
        - 若AD_copilot_ai_script_recommendation_log中状态=SUCCESS，直接返回SUCCESS（含剧本），终止流程
        - 若状态=FAILURE，将记录更新为PROCESSING，重新触发异步处理流程
        - 若不存在，正常执行后续步骤
  - rule: 配置校验
    description: |
      请求参数aiExecuteCode必须在AD_copilot_ai_execute_config表中存在，且对应记录的agent_workflow_code必须等于'25b65c76c7054f9785f303bc92d0c0b6'。
      若不满足，返回422 (ai执行编号不存在)。
  - rule: 基准获取
    description: |
      从AD_copilot_ai_script_recommendation_log表中查询当日（按updated_at）该uid+source的最新记录，提取其input_data字段作为基准数据（注意input_data为json字符串，必须包含uid字段)。
      若不存在任何记录，返回422 (未找到离线数据)。
  - rule: 特征更新
    description: |
      根据featureComputeRequest.featureConfigs中的配置，调用Feature_SDK获取实时特征值。
      更新规则：
        1. 仅当基准input_data中已存在与alias同名的字段时，才用特征值覆盖。
        2. 特征值必须非null且获取成功（无超时、无key错误），否则跳过。
        3. 覆盖时完全替换原值。
        4. 基准中其他字段保持不变，不新增字段。
  - rule: 注记更新
    description: |
      若请求体中inputData.contents存在且为非空字符串，则用该值覆盖基准input_data中的contents字段。
      否则保留基准中的原contents值。
  - rule: 异步处理
    description: |
      在AD_copilot_ai_script_recommendation_log表中插入状态为PROCESSING的记录后，立即发送MQ消息。
      后台消费者接收消息后调用AI平台生成剧本，并根据结果更新：
        - 成功：AD_copilot_ai_script_recommendation_log状态置为SUCCESS，output_data存入AI返回结果，并Upsert AD_copilot_ai_script_recommendation（基于uid+source）
        - 失败：AD_copilot_ai_script_recommendation_log状态置为FAILURE，failure_reason记录错误信息

# -------------------- 请求参数 --------------------
request:
  headers:
    Content-Type:
      required: true
      value: application/json
      description: 必须为application/json
  path: {}
  query: {}
  body:
    required: true
    content_type: application/json
    schema:
      type: object
      properties:
        serial_id:
          type: string
          maxLength: 64
          required: true
          description: UUID格式，全局唯一，用于幂等
          example: "c96660e776d84955b810a83da5b18767"
        uid:
          type: string
          maxLength: 64
          required: true
          description: 用户ID
          example: "504ac82116e611f1bb119c63c059e356"
        source:
          type: string
          maxLength: 50
          required: true
          enum: [postLoan, electricPin, service]
          description: 业务来源
          example: "autotest2"
        trigerScene:
          type: string
          maxLength: 50
          required: true
          enum: [JOB, REPAY_SUCCESS, AI_SUMMARY_SUCCESS]
          description: 触发场景
          example: "REPAY_SUCCESS"
        aiExecuteCode:
          type: string
          maxLength: 100
          required: false
          description: AI执行配置编号，必须在AD_copilot_ai_execute_config中存在且满足agent_workflow_code条件
          example: "AI_SCRIPT_RECOMMANDATION_2"
        queue:
          type: string
          maxLength: 100
          required: false
          description: 用户所属队列（业务标识）
          example: "ai_play_queue_22"
        inputData:
          type: object
          required: false
          description: 加工好的业务数据
          properties:
            contents:
              type: string
              required: false
              description: 注记内容，非空时覆盖基准
              example: "工单内容：用户进线，咨询逾期账单费用减免..."
        featureComputeRequest:
          type: object
          required: false
          description: 特征计算请求
          properties:
            bizSerial:
              type: string
              maxLength: 64
              required: false
              description: 特征请求幂等标识，随机UUID
              example: "8727575b4b9c4d38b29f8ec26fcc2694"
            uid:
              type: string
              maxLength: 64
              required: false
              description: 用户ID，需与顶层uid一致
              example: "504ac82116e611f1bb119c63c059e356"
            commonParams:
              type: object
              required: false
              properties:
                uid:
                  type: string
                  maxLength: 64
                  required: false
                  example: "504ac82116e611f1bb119c63c059e356"
                caseNumber:
                  type: string
                  required: false
                  description: 催收案件编号
            featureConfigs:
              type: array
              required: false
              items:
                type: object
                properties:
                  featureKey:
                    type: string
                    required: false
                    description: SDK查询key
                    example: "rt_usr_adt_rat_csh"
                  alias:
                    type: string
                    required: false
                    description: 映射到input_data的字段名
                    example: "overdueCnt"
  example:
    value: |
      {
          "serial_id": "c96660e776d84955b810a83da5b18767=",
          "uid": "504ac82116e611f1bb119c63c059e356",
          "source": "autotest2",
          "triger_scene": "REPAY_SUCCESS",
          "aiExecuteCode": "AI_SCRIPT_RECOMMANDATION_2=",
          "queue": "ai_play_queue",
          "inputData": {
              "contents": "工单内容：用户进线，咨询逾期账单费用减免，辛苦处理。 工单处理：沟通中无故挂断，告知没有政策帮助，五点主动处理完成?"
          },
          "featureComputeRequest": {
              "bizSerial": "8727575b4b9c4d38b29f8ec26fcc2694",
              "uid": "504ac82116e611f1bb119c63c059e356",
              "commonParams": {
                  "uid": "504ac82116e611f1bb119c63c059e356",
                  "caseNumber": "case14933_200000012"
              },
              "featureConfigs": [
                  {
                      "featureKey": "rt_usr_adt_rat_csh",
                      "alias": "overdueCnt"
                  },
                  {
                      "featureKey": "clc_usr_iso_sex=",
                      "alias": "sex"
                  },
                  {
                      "featureKey": "tel_usr_adj_lmt",
                      "alias": "callCnt="
                  }
              ]
          }
      }

# -------------------- 响应参数 --------------------
response:
  status:
    200:
      description: 成功响应（包括首次调用返回PROCESSING、幂等命中返回SUCCESS/FAILURE）
      headers: {}
      body:
        type: object
        properties:
          serial_id:
            type: string
            description: 流水号回显
          uid:
            type: string
            description: 用户ID回显
          generateStatus:
            type: string
            enum: [PROCESSING, SUCCESS, FAILURE]
            description: 生成状态（客户端可能收到PROCESSING/SUCCESS/FAILURE，INIT不对外返回）
          generateTime:
            type: integer
            format: int64
            description: 完成时间戳（Unix毫秒），仅当generateStatus为SUCCESS或FAILURE时返回
          scriptContent:
            type: object
            required: false
            description: AI剧本内容，仅generateStatus=SUCCESS时返回
            properties:
              character:
                type: string
              target:
                type: string
              pressure_points:
                type: array
                items:
                  type: object
                  properties:
                    point:
                      type: string
                    script:
                      type: array
                      items:
                        type: string
              resp_code:
                type: string
                description: AI平台业务状态码（"1":成功，"0":失败）
              resp_msg:
                type: string
                description: 失败时的错误信息
      examples:
        - scenario: 首次调用成功，返回PROCESSING
          value: |
            {
                "generateStatus": "PROCESSING",
                "generateTime": 1773306321658,
                "serialId": "c96660e776d84955b810a83da5b18767=",
                "uid": "5d9f39a330984c70b8341fdd9e449398"
            }
        - scenario: 幂等命中SUCCESS
          value: |
            {
                "generateStatus": "SUCCESS",
                "generateTime": 1773306322000,
                "scriptContent": {
                    "character": "贷后管理部",
                    "pressure_points": [
                        {
                            "point": "探究客户的实际还款能力…",
                            "script": ["询问收入和负债…", "强调资金用途和责任…"]
                        },
                        {
                            "point": "让客户认识到频繁借款…",
                            "script": ["督促维护信用…", "警告后果…"]
                        }
                    ],
                    "resp_code": "1",
                    "resp_msg": "success",
                    "target": "本人"
                },
                "serialId": "c96660e776d84955b810a83da5b18767=",
                "uid": "5d9f39a330984c70b8341fdd9e449398"
            }
        - scenario: 幂等命中FAILURE，重新调用并返回PROCESSING
          value: |
            {
                "generateStatus": "PROCESSING",
                "generateTime": 1773306321658,
                "serialId": "c96660e776d84955b810a83da5b18767=",
                "uid": "5d9f39a330984c70b8341fdd9e449398"
            }
    422:
      description: 请求参数校验失败
      headers: {}
      body:
        type: object
        properties:
          code:
            type: string
            description: 错误码
          message:
            type: string
            description: 错误描述
      examples:
        - scenario: ai执行编号不存在
          value: |
            {
                "code": 40001,
                "errorLevel": "1",
                "message": "ai执行编号不存在",
                "status": 422
            }
        - scenario: 未找到离线数据
          value: |
            {
                "code": 40002,
                "errorLevel": "1",
                "message": "未找到离线数据",
                "status": 422
            }

# -------------------- 测试数据（真实可用）--------------------
test_data:
  agent_workflow_code: "25b65c76c7054f9785f303bc92d0c0b6"
  feature_configs:
    - alias: "overdueCnt"
      featureKey: "rt_usr_adt_rat_csh"
      featureValue: 35.99
      description: "有效alias、有效featureKey，返回固定值35.99"
    - alias: "sex"
      featureKey: "clc_usr_iso_sex="
      featureValue: null
      description: "有效alias、无效featureKey，返回null"
    - alias: "callCnt="
      featureKey: "tel_usr_adj_lmt"
      featureValue: 1
      description: "无效alias（带特殊字符）、有效featureKey，返回值1"

# -------------------- 注释--------------------
notes: []

```


---

### 支撑/依赖知识要素
> **注意**：以下知识要素仅作为辅助知识，用于【准备测试数据】、【提供表结构】或【理解业务约束】、【预期结果断言】。**不需要**针对这些依赖知识要素单独设计用例。

#### AD_copilot_ai_script_recommendation_log - 剧本推荐日志表
```yaml
type: AD-系统数据类
code: AD_copilot_ai_script_recommendation_log
name: 剧本推荐日志表
version: v2.0
description: 记录每次剧本生成请求的详细日志，包含输入输出、状态和失败原因
keys:
  type: MySQL
  database: copilot
  table: ai_script_recommendation_log
ddl: |
    CREATE TABLE `ai_script_recommendation_log` (
      `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
      `serial_id` varchar(64) NOT NULL COMMENT '流水号',
      `uid` varchar(64) NOT NULL COMMENT '客户uid',
      `queue` varchar(100) DEFAULT NULL COMMENT '案件当前所属的队列',
      `ai_execute_code` varchar(100) DEFAULT NULL COMMENT 'ai执行编号',
      `triger_scene` varchar(50) NOT NULL COMMENT '触发剧本更新的场景：JOB，REPAY_SUCCESS，AI_SUMMARY_SUCCESS',
      `input_data` text COMMENT 'JSON字符串，调用智能平台传入的加工好的业务数据，必须包含主键 uid',
      `output_data` text COMMENT 'JSON字符串，智能平台返回的结果内容',
      `execute_status` varchar(20) NOT NULL COMMENT '执行状态：INIT，SUCCESS，FAILURE，PROCESSING',
      `failure_reason` varchar(500) DEFAULT NULL COMMENT '失败原因：执行异常、匹配剧本失败 等失败原因',
      `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
      `source` varchar(50) NOT NULL COMMENT '业务来源 postLoan:贷后，electricPin:电销，service:客服',
      PRIMARY KEY (`id`),
      UNIQUE KEY `uk_serial_id` (`serial_id`) USING BTREE,
      KEY `idx_uid` (`uid`) USING BTREE,
      KEY `idx_updated_at` (`updated_at`) USING BTREE,
      KEY `idx_created_at` (`created_at`) USING BTREE
    ) ENGINE=InnoDB COMMENT='智能剧本推荐记录日志表';
test_data:
  complete:
    serial_id: "uuid-complete-001"
    uid: "100002"
    queue: "S1"
    ai_execute_code: "SCRIPT_GEN_001"
    triger_scene: "JOB"
    input_data: '{"income":"5千-1万","isFirstOverdue":"0","contactNameFst":"王五","companyName":"XX科技公司","identAddress":"北京市朝阳区","loanCnt":"3","uid":"0e5d1ede6d484c328dc9074746975d81","complainCnt":"0","latestOutcallStatus":"1","laterstAiCallSummary":"客户质疑平台政策，要求减免费用，情绪激动","overdueDays":"15","callCnt":"20","totalOverdueAmount":"5000.00","latestRepayTime":"2026-01-15 10:30:00","callAnswerRate":"0.8500","totalOverduePrincipal":"4000.00","sex":"男","degree":"本科","laterstManualCallSummary":"沟通中无故挂断，告知没有政策帮助","overdueCnt":"1","customerName":"张三","monthRepayAmount":"1500.00","contactRelationFst":"USER_RELATION_PARENT","queueName":"ai_play_queue_1","contents":"用户进线，咨询逾期账单费用减免，辛苦处理","concatCnt":"10","latestSixMonthOverdueCnt":"2","deviceModel":"iPhone12,1","age":"30","maritalStatus":"已婚"}'
    execute_status: "SUCCESS"
    output_data: '{"character":"还呗财务部","target":"本人","pressure_points":[{"point":"施压点1","script":["话术11","话术12"]},{"point":"施压点2","script":["话术21","话术22"]}],"resp_code":"1","resp_msg":"success"}'
    source: "postLoan"

queries:
  - purpose: 验证JSON字段值（必须使用JSON_UNQUOTE）
    sql: "SELECT JSON_UNQUOTE(JSON_EXTRACT(output_data, '$.resp_code')) as resp_code, JSON_UNQUOTE(JSON_EXTRACT(output_data, '$.character')) as character FROM ai_script_recommendation_log WHERE source = ? ORDER BY id DESC LIMIT 1"
  - purpose: 查询待处理记录（INIT/FAILURE/PROCESSING，且超过一定时间）
    sql: "SELECT id, serial_id, uid, queue, ai_execute_code, input_data, source FROM ai_script_recommendation_log WHERE execute_status = ? AND updated_at < DATE_SUB(NOW(), INTERVAL ? MINUTE) ORDER BY updated_at ASC LIMIT ?"
  - purpose: 验证所有记录的状态一致
    sql: "SELECT COUNT(*) as total_count, SUM(CASE WHEN execute_status = 'SUCCESS' THEN 1 ELSE 0 END) as success_count FROM ai_script_recommendation_log WHERE source = ?"
notes:
  - 数据准备顺序：建议先清理历史数据（如根据source和日期），再插入新数据，避免冲突。
  - input_data 模型输入数据，必须包含主键 uid。
  - JSON字段提取必须使用JSON_UNQUOTE(JSON_EXTRACT(...))，否则返回带引号的字符串。
  - 异步执行有60-120秒延迟，断言时需设置timeout（如60秒）和poll_interval（如3秒）。
  - 关联知识要素：AD_common_job_status（Job状态表）通过source字段关联。
```

#### AD_copilot_ai_execute_config - AI执行配置表
```yaml
type: AD-系统数据类
code: AD_copilot_ai_execute_config
name: AI执行配置表
version: v2.0
description: 存储AI工作流/模型的配置信息，用于校验请求中的aiExecuteCode合法性

keys:
  type: MySQL
  database: copilot
  table: ai_execute_config
ddl: |
    CREATE TABLE `ai_execute_config` (
      `id` bigint(32) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
      `name` varchar(64) DEFAULT NULL COMMENT '业务名字',
      `code` varchar(32) DEFAULT NULL COMMENT '业务编号',
      `type` varchar(32) DEFAULT NULL COMMENT '工作流：flow，模型：model',
      `agent_workflow_code` varchar(100) DEFAULT NULL COMMENT '智能体/工作流的code',
      `source` varchar(20) DEFAULT NULL COMMENT '业务线:postLoan,electricPin,telmarket',
      `model_info` varchar(64) DEFAULT NULL COMMENT '模型信息',
      `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
      PRIMARY KEY (`id`),
      KEY `idx_code` (`code`) USING BTREE,
      KEY `idx_updated_at` (`updated_at`) USING BTREE
    ) ENGINE=InnoDB COMMENT='AI执行配置表';
logic_rules: []
test_data: []
notes:
  - 新增业务线或工作流时，必须先在此表添加配置记录。
  - 可通过配置无效的agent_workflow_code，来测试AI执行接口的校验逻辑。
  - code 字段与AD_copilot_ai_script_recommendation_log表、AD_copilot_ai_script_recommendation表、AI_copilot_ai_script_generate请求体中的ai_execute_code字段对应。
```

#### AD_copilot_ai_script_recommendation - 剧本推荐表
```yaml
type: AD-系统数据类
code: AD_copilot_ai_script_recommendation
name: 剧本推荐表
version: v2.0
description: 存储每个用户在每个业务来源下的最新AI剧本结果，用于快速查询
keys:
  type: MySQL
  database: copilot
  table: ai_script_recommendation
  ddl: |
    CREATE TABLE `ai_script_recommendation` (
      `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
      `serial_id` varchar(64) NOT NULL COMMENT '流水号',
      `uid` varchar(64) NOT NULL COMMENT '客户uid',
      `queue` varchar(100) DEFAULT NULL COMMENT '案件当前所属的队列',
      `triger_scene` varchar(50) NOT NULL COMMENT '触发剧本更新的场景',
      `source` varchar(50) NOT NULL COMMENT '业务来源',
      `ai_execute_code` varchar(100) DEFAULT NULL COMMENT 'ai执行编号',
      `output_data` text COMMENT '智能平台返回的结果内容',
      `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
      PRIMARY KEY (`id`),
      UNIQUE KEY `uk_uid_source` (`uid`,`source`) USING BTREE,
      KEY `idx_updated_at` (`updated_at`) USING BTREE
    ) ENGINE=InnoDB COMMENT='智能剧本推荐表';
business_rules: []
test_data:
  minimal_valid:
    serial_id: "uuid-min-001"
    uid: "100001"
    source: "postLoan"
    triger_scene: "JOB"
    output_data: '{"character":"还呗财务部","target":"本人","pressure_points":[{"point":"施压点1","script":["话术11","话术12"]},{"point":"施压点2","script":["话术21","话术22"]}],"resp_code":"1","resp_msg":"success"}'
  complete:
    serial_id: "uuid-complete-001"
    uid: "100002"
    queue: "S1"
    triger_scene: "JOB"
    source: "postLoan"
    ai_execute_code: "SCRIPT_GEN_001"
    output_data: '{"character":"还呗财务部","target":"本人","pressure_points":[{"point":"施压点1","script":["话术11","话术12"]},{"point":"施压点2","script":["话术21","话术22"]}],"resp_code":"1","resp_msg":"success"}'
queries:
  - purpose: 查询用户当日最新剧本
    sql: "SELECT serial_id, queue, output_data, updated_at FROM ai_script_recommendation WHERE uid = ? AND source = ? AND DATE(updated_at) = CURDATE()"
notes: []
```



## 3. 测试生成任务指令 (Task Instructions)


请基于提供的【核心测试目标】及其【支撑知识】，遵循【系统提示词】规范，自动推理并生成一套**完备且逻辑联动**的 YAML 测试用例集。

### A. 全路径逻辑覆盖 (Logic Coverage)
- **分支推导**：深度解析目标知识要素的 `logic_rules` 及支撑知识要素中的 `logic_rules`。
- **场景要求**：必须输出覆盖全逻辑分支的用例，包括核心成功路径、规则校验失败路径、参数异常边界及异步状态流转场景。

### B. 自动化数据建模与联动 (Data Linkage)
- **环境构造**：识别目标知识要素依赖的支撑知识要素。在 `preconditions` 中使用 `database_insert` 动作，根据其 DDL 定义为每个用例铺设精准的存量数据。
- **标识符接力**：
  - **识别唯一键**：自动识别支撑知识要素中的**主键 (PK)**、**唯一索引 (Unique Key)** 或**业务关联字段**。
  - **动态引用**：在 `preconditions` 中由 **TF (函数)** 产生的任何动态标识符，必须通过 `${context.var}` 在后续 `test_steps` 的入参及 `assertions` 的查询条件中进行**精准联动引用**。严禁各步骤间出现逻辑断层或硬编码。

### C. 闭环验证设计 (Assertion Logic)
- **实时与终态校验**：
  - 每个用例必须包含对核心执行结果（如 API 返回、Job 状态）的校验。
  - 必须根据支撑知识要素 **AD (数据类)** 的定义，如使用 `assert_database_field` 验证业务执行后数据库字段的**最终业务状态**。
  - 针对异步落库链路，必须包含 `timeout` 轮询断言。

### D. 规范执行要求
- **语义化命名**：严格遵守 `[核心动作]_[测试场景/输入条件]_[预期结果]` 的中文命名规范。
- **参数一致性**：YAML 脚本中的所有参数 Key 必须与知识要素定义中的 DDL 字段或 API 字段名严格保持一致。

