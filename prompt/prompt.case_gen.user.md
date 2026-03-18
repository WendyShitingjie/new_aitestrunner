# 用户提示词 (User Prompt)

## 1. 核心测试目标 (Core Test Target)
> **注意**：以下知识要素是本次测试的主体。请深入解析该知识要素的定义，识别其业务逻辑分支、入参约束及潜在的失败场景。

### 【目标知识要素：AI-系统接口类】AI_copilot_ai_script_generate - AI剧本实时生成
```yaml
type: AI-系统接口类知识要素
id: AI_copilot_ai_script_generate
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
  - name: AD_copilot_ai_script_recommendation_log
    type: MySQL
    description: 剧本推荐日志表，存储流水状态、input_data、AI返回结果output_data
    operations:
      - operation: read
        purpose: 幂等校验（查询serial_id是否存在）及获取基准数据（查询uid+source+updated_at最新记录）
        key_fields: [serial_id, uid, aiExecuteCode, source, updated_at]
      - operation: write
        purpose: 插入新流水（状态INIT）、中间状态（PROCESSING）及最终状态（SUCCESS/FAILURE）及结果
        key_fields: [serial_id, uid, queue, aiExecuteCode, triger_scene, source, execute_status, input_data, output_data, failure_reason]
        
  - name: AD_copilot_ai_execute_config
    type: MySQL
    description: AI执行配置表，存储AI配置信息
    operations:
      - operation: read
        purpose: 校验code=AD_copilot_ai_script_recommendation_log.aiExecuteCode是否存在
        key_fields: [ source, code, agent_workflow_code ]
        
  - name: AD_copilot_ai_script_recommendation
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
notes:

```

---


```

## 2. 测试场景规划任务 (Scenario Planning Instructions)

请基于上述目标知识要素的定义，遵循【系统提示词】规范，推导并规划全路径覆盖的自动化测试场景集。

### A. 逻辑分支拆解 (Logical Branching)
- **自主推导**：解析知识要素 `logic_rules` 中的每一个判定点（如：uid有效性、策略类型分支、频率限制）。
- **规划场景**：
    - **正向全流程**：覆盖核心业务成功的路径。
    - **逆向逻辑分支**：根据规则推导出预期的失败场景（如：配置未激活、策略匹配失败、频率触发限流等）。
    - **参数边界**：推导参数缺失、格式非法等基础校验场景。

### B. 依赖关系识别 (Dependency Identification)
- **需求识别**：在此阶段，你需根据知识要素逻辑**预判**执行该场景可能涉及的支撑知识类型（如：需要哪个表的数据铺底、需要哪条业务规则判定）。
- **清单列出**：在每个场景的 `dependent_elements` 中列出你认为需要的支撑知识要素编码或描述（作为第二阶段的数据申请清单）。

### C. 意图结构化描述 (Intent Description)
- **前置意图**：清晰描述需要执行的“环境清理”和“数据铺底”逻辑。
- **步骤与断言意图**：描述需要执行的操作动作，以及需要验证的实时响应和数据库终态（指出需要验证哪些表、哪些字段的状态）。

### D. 输出约束
- **严禁输出具体 Params**：不要猜测具体的 DDL 字段或参数细节，仅描述“意图”。
- **命名规范**：`test_name` 必须严格遵守 `[动作]_[场景]_[结果]` 中文规范。
- **YAML Value**：所有字符串值必须使用双引号包裹。

