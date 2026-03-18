<thinking>
1. DDL分析：
   - AD_copilot_ai_script_recommendation_log表主键为id(自增)，唯一键为uk_serial_id(serial_id)
   - 非空字段：serial_id, uid, triger_scene, execute_status, source
   - AD_copilot_ai_execute_config表主键为id(自增)，索引为idx_code(code)
   - 非空字段：id(自增，无需插入时指定)
   - AD_copilot_ai_script_recommendation表主键为id(自增)，唯一键为uk_uid_source(uid,source)
   - 非空字段：serial_id, uid, triger_scene, source

2. 场景拆解：
   - 正向场景：合法参数，配置存在，基准数据存在，异步成功
   - 异常场景1：aiExecuteCode不存在
   - 异常场景2：未找到离线数据
   - 异常场景3：幂等处理(SUCCESS状态)
   - 异常场景4：幂等处理(FAILURE状态，重新触发)

3. 业务规则深度解析：
   - 幂等处理：相同serial_id不同状态的处理逻辑
   - 配置校验：aiExecuteCode必须存在且agent_workflow_code='25b65c76c7054f9785f303bc92d0c0b6'
   - 基准获取：按uid+source查询最新记录的input_data
   - 特征更新：仅覆盖已存在的字段
   - 注记更新：覆盖contents字段
   - 异步处理：立即返回PROCESSING，后台异步处理

4. 数据清理与构造：
   - 清理：根据serial_id清理ai_script_recommendation_log
   - 构造：插入必要的配置数据和基准数据
</thinking>

```yaml
# TC1: 正向场景 - 首次调用成功返回PROCESSING
- case_code: "TC_AI_copilot_ai_script_generate_001"
  case_name: "AI剧本信息实时生成_合法参数首次调用_返回PROCESSING"
  element_code: "AI_copilot_ai_script_generate"
  element_name: "AI剧本信息实时生成"
  priority: "P0"
  auto_level: "L3"
  
  dependent_elements:
    - element_code: "AD_copilot_ai_execute_config"
      element_name: "AI执行配置表"
    - element_code: "AD_copilot_ai_script_recommendation_log"
      element_name: "剧本推荐日志表"
    - element_code: "AD_copilot_ai_script_recommendation"
      element_name: "剧本推荐表"
  
  test_intent:
    preconditions:
      - intent: "前置1：清理历史数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          where: "serial_id='test_serial_001' OR uid='test_user_001'"
      
      - intent: "前置2：清理配置历史"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_execute_config"
          where: "code='AI_SCRIPT_TEST_001'"
      
      - intent: "前置3：插入AI执行配置"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_execute_config"
          data:
            name: "测试AI剧本生成配置"
            code: "AI_SCRIPT_TEST_001"
            type: "flow"
            agent_workflow_code: "25b65c76c7054f9785f303bc92d0c0b6"
            source: "postLoan"
      
      - intent: "前置4：插入基准数据"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          data:
            serial_id: "${uuid()}"
            uid: "test_user_001"
            queue: "ai_test_queue"
            ai_execute_code: "AI_SCRIPT_TEST_001"
            triger_scene: "REPAY_SUCCESS"
            input_data: "{\"uid\":\"test_user_001\",\"overdueCnt\":10,\"sex\":\"男\",\"contents\":\"基准内容\"}"
            execute_status: "SUCCESS"
            source: "postLoan"
    
    test_steps:
      - intent: "步骤1：调用AI剧本生成接口"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          body:
            serial_id: "test_serial_001"
            uid: "test_user_001"
            source: "postLoan"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "AI_SCRIPT_TEST_001"
            queue: "ai_test_queue"
            inputData:
              contents: "新的工单内容：用户进线，咨询逾期账单费用减免"
            featureComputeRequest:
              bizSerial: "${uuid()}"
              uid: "test_user_001"
              commonParams:
                uid: "test_user_001"
              featureConfigs:
                - featureKey: "rt_usr_adt_rat_csh"
                  alias: "overdueCnt"
        assertions:
          - intent: "断言1：验证API返回状态码"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 200
          - intent: "断言2：验证返回状态为PROCESSING"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.generateStatus}"
              expected: "PROCESSING"
          - intent: "断言3：验证序列号回显正确"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.serialId}"
              expected: "test_serial_001"
          - intent: "断言4：验证日志表中记录状态为PROCESSING"
            action: "assert_database_field"
            params:
              database: "copilot"
              table: "ai_script_recommendation_log"
              field: "execute_status"
              where: "serial_id='test_serial_001'"
              expected: "PROCESSING"
              timeout: 30
              interval: 3

# TC2: 异常场景 - aiExecuteCode不存在
- case_code: "TC_AI_copilot_ai_script_generate_002"
  case_name: "AI剧本信息实时生成_ai执行编号不存在_返回422错误"
  element_code: "AI_copilot_ai_script_generate"
  element_name: "AI剧本信息实时生成"
  priority: "P0"
  auto_level: "L3"
  
  dependent_elements:
    - element_code: "AD_copilot_ai_execute_config"
      element_name: "AI执行配置表"
    - element_code: "AD_copilot_ai_script_recommendation_log"
      element_name: "剧本推荐日志表"
  
  test_intent:
    preconditions:
      - intent: "前置1：清理历史数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          where: "serial_id='test_serial_002'"
    
    test_steps:
      - intent: "步骤1：调用AI剧本生成接口（无效配置代码）"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          body:
            serial_id: "test_serial_002"
            uid: "test_user_002"
            source: "postLoan"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "INVALID_CODE_001"
            queue: "ai_test_queue"
        assertions:
          - intent: "断言1：验证返回状态码为422"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 422
          - intent: "断言2：验证错误消息"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.message}"
              expected: "ai执行编号不存在"

# TC3: 异常场景 - 未找到离线数据
- case_code: "TC_AI_copilot_ai_script_generate_003"
  case_name: "AI剧本信息实时生成_未找到基准数据_返回422错误"
  element_code: "AI_copilot_ai_script_generate"
  element_name: "AI剧本信息实时生成"
  priority: "P0"
  auto_level: "L3"
  
  dependent_elements:
    - element_code: "AD_copilot_ai_execute_config"
      element_name: "AI执行配置表"
    - element_code: "AD_copilot_ai_script_recommendation_log"
      element_name: "剧本推荐日志表"
  
  test_intent:
    preconditions:
      - intent: "前置1：清理历史数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          where: "serial_id='test_serial_003' OR uid='test_user_003'"
      
      - intent: "前置2：清理配置历史"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_execute_config"
          where: "code='AI_SCRIPT_TEST_003'"
      
      - intent: "前置3：插入有效的AI执行配置"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_execute_config"
          data:
            name: "测试AI剧本生成配置"
            code: "AI_SCRIPT_TEST_003"
            type: "flow"
            agent_workflow_code: "25b65c76c7054f9785f303bc92d0c0b6"
            source: "postLoan"
    
    test_steps:
      - intent: "步骤1：调用AI剧本生成接口（无基准数据）"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          body:
            serial_id: "test_serial_003"
            uid: "test_user_003"
            source: "postLoan"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "AI_SCRIPT_TEST_003"
            queue: "ai_test_queue"
        assertions:
          - intent: "断言1：验证返回状态码为422"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 422
          - intent: "断言2：验证错误消息"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.message}"
              expected: "未找到离线数据"

# TC4: 幂等处理 - SUCCESS状态直接返回
- case_code: "TC_AI_copilot_ai_script_generate_004"
  case_name: "AI剧本信息实时生成_幂等处理SUCCESS状态_直接返回成功结果"
  element_code: "AI_copilot_ai_script_generate"
  element_name: "AI剧本信息实时生成"
  priority: "P1"
  auto_level: "L3"
  
  dependent_elements:
    - element_code: "AD_copilot_ai_execute_config"
      element_name: "AI执行配置表"
    - element_code: "AD_copilot_ai_script_recommendation_log"
      element_name: "剧本推荐日志表"
  
  test_intent:
    preconditions:
      - intent: "前置1：清理历史数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          where: "serial_id='test_serial_004' OR uid='test_user_004'"
      
      - intent: "前置2：插入已成功的记录"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          data:
            serial_id: "test_serial_004"
            uid: "test_user_004"
            queue: "ai_test_queue"
            ai_execute_code: "AI_SCRIPT_TEST_004"
            triger_scene: "REPAY_SUCCESS"
            input_data: "{\"uid\":\"test_user_004\",\"overdueCnt\":5,\"contents\":\"基准内容\"}"
            output_data: "{\"character\":\"还呗财务部\",\"target\":\"本人\",\"pressure_points\":[{\"point\":\"施压点1\",\"script\":[\"话术11\",\"话术12\"]}],\"resp_code\":\"1\",\"resp_msg\":\"success\"}"
            execute_status: "SUCCESS"
            source: "postLoan"
    
    test_steps:
      - intent: "步骤1：再次调用AI剧本生成接口（幂等）"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          body:
            serial_id: "test_serial_004"
            uid: "test_user_004"
            source: "postLoan"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "AI_SCRIPT_TEST_004"
            queue: "ai_test_queue"
        assertions:
          - intent: "断言1：验证返回状态码为200"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 200
          - intent: "断言2：验证返回状态为SUCCESS"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.generateStatus}"
              expected: "SUCCESS"
          - intent: "断言3：验证返回了剧本内容"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.scriptContent.character}"
              expected: "还呗财务部"
          - intent: "断言4：验证日志表状态仍为SUCCESS"
            action: "assert_database_field"
            params:
              database: "copilot"
              table: "ai_script_recommendation_log"
              field: "execute_status"
              where: "serial_id='test_serial_004'"
              expected: "SUCCESS"

# TC5: 幂等处理 - FAILURE状态重新触发
- case_code: "TC_AI_copilot_ai_script_generate_005"
  case_name: "AI剧本信息实时生成_幂等处理FAILURE状态_更新为PROCESSING重新触发"
  element_code: "AI_copilot_ai_script_generate"
  element_name: "AI剧本信息实时生成"
  priority: "P1"
  auto_level: "L3"
  
  dependent_elements:
    - element_code: "AD_copilot_ai_execute_config"
      element_name: "AI执行配置表"
    - element_code: "AD_copilot_ai_script_recommendation_log"
      element_name: "剧本推荐日志表"
  
  test_intent:
    preconditions:
      - intent: "前置1：清理历史数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          where: "serial_id='test_serial_005' OR uid='test_user_005'"
      
      - intent: "前置2：清理配置历史"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_execute_config"
          where: "code='AI_SCRIPT_TEST_005'"
      
      - intent: "前置3：插入AI执行配置"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_execute_config"
          data:
            name: "测试AI剧本生成配置"
            code: "AI_SCRIPT_TEST_005"
            type: "flow"
            agent_workflow_code: "25b65c76c7054f9785f303bc92d0c0b6"
            source: "postLoan"
      
      - intent: "前置4：插入失败状态的记录"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          data:
            serial_id: "test_serial_005"
            uid: "test_user_005"
            queue: "ai_test_queue"
            ai_execute_code: "AI_SCRIPT_TEST_005"
            triger_scene: "REPAY_SUCCESS"
            input_data: "{\"uid\":\"test_user_005\",\"overdueCnt\":5,\"contents\":\"基准内容\"}"
            execute_status: "FAILURE"
            failure_reason: "AI平台调用超时"
            source: "postLoan"
    
    test_steps:
      - intent: "步骤1：再次调用AI剧本生成接口（失败后重试）"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          body:
            serial_id: "test_serial_005"
            uid: "test_user_005"
            source: "postLoan"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "AI_SCRIPT_TEST_005"
            queue: "ai_test_queue"
        assertions:
          - intent: "断言1：验证返回状态码为200"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 200
          - intent: "断言2：验证返回状态为PROCESSING"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.generateStatus}"
              expected: "PROCESSING"
          - intent: "断言3：验证日志表状态已更新为PROCESSING"
            action: "assert_database_field"
            params:
              database: "copilot"
              table: "ai_script_recommendation_log"
              field: "execute_status"
              where: "serial_id='test_serial_005'"
              expected: "PROCESSING"
              timeout: 30
              interval: 3
          - intent: "断言4：验证失败原因被清空"
            action: "assert_database_field"
            params:
              database: "copilot"
              table: "ai_script_recommendation_log"
              field: "failure_reason"
              where: "serial_id='test_serial_005'"
              expected: ""
```