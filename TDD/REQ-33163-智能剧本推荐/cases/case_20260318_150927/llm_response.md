<thinking>
1. DDL分析：
   - AD_copilot_ai_script_recommendation_log表：主键id(自增)，唯一键uk_serial_id(serial_id)，非空字段包括serial_id, uid, triger_scene, execute_status, source
   - AD_copilot_ai_execute_config表：主键id(自增)，索引idx_code(code)
   - AD_copilot_ai_script_recommendation表：主键id(自增)，唯一键uk_uid_source(uid,source)

2. 场景拆解：根据AI_copilot_ai_script_generate的logic_rules，需要覆盖：
   - 正向场景：合法参数，返回PROCESSING，异步完成后SUCCESS
   - 幂等处理：相同serial_id，SUCCESS状态直接返回，FAILURE状态重新处理
   - 配置校验失败：aiExecuteCode不存在或agent_workflow_code不匹配
   - 基准获取失败：未找到uid+source的最新记录

3. 数据清理与构造：需要先清理相关表的历史数据，然后插入必要的基础数据
</thinking>

```yaml
# 用例1：正向场景 - 合法参数提交，返回PROCESSING，异步完成后SUCCESS
- case_code: "TC_AI_copilot_ai_script_generate_001"
  case_name: "AI剧本信息实时生成_合法参数提交_返回PROCESSING并异步成功"
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
          where: "uid='test_user_001' AND source='postLoan'"
      
      - intent: "前置2：清理配置表数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_execute_config"
          where: "code='AI_SCRIPT_TEST_001'"
      
      - intent: "前置3：清理剧本推荐表数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_script_recommendation"
          where: "uid='test_user_001' AND source='postLoan'"
      
      - intent: "前置4：插入AI执行配置"
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
      
      - intent: "前置5：插入基准数据（模拟已有记录）"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          data:
            serial_id: "${uuid()}"
            uid: "test_user_001"
            queue: "ai_play_queue_test"
            ai_execute_code: "AI_SCRIPT_TEST_001"
            triger_scene: "REPAY_SUCCESS"
            input_data: "{\"uid\":\"test_user_001\",\"overdueCnt\":2,\"contents\":\"基准内容\"}"
            execute_status: "SUCCESS"
            output_data: "{\"character\":\"基准角色\",\"target\":\"本人\"}"
            source: "postLoan"
    
    test_steps:
      - intent: "步骤1：调用AI剧本生成接口"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          headers:
            Content-Type: "application/json"
          body:
            serial_id: "${uuid()}"
            uid: "test_user_001"
            source: "postLoan"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "AI_SCRIPT_TEST_001"
            queue: "ai_play_queue_test"
            inputData:
              contents: "新的工单内容"
            featureComputeRequest:
              bizSerial: "${uuid()}"
              uid: "test_user_001"
              commonParams:
                uid: "test_user_001"
              featureConfigs:
                - featureKey: "rt_usr_adt_rat_csh"
                  alias: "overdueCnt"
        assertions:
          - intent: "断言1：校验API响应状态码"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 200
          
          - intent: "断言2：校验API响应中generateStatus为PROCESSING"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.generateStatus}"
              expected: "PROCESSING"
          
          - intent: "断言3：校验数据库中记录状态变为PROCESSING"
            action: "assert_database_field"
            params:
              database: "copilot"
              table: "ai_script_recommendation_log"
              field: "execute_status"
              where: "uid='test_user_001' AND source='postLoan' AND execute_status='PROCESSING'"
              expected: "PROCESSING"
              timeout: 30
              interval: 2
      
      - intent: "步骤2：等待异步处理完成，校验最终状态为SUCCESS"
        action: "assert_database_field"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          field: "execute_status"
          where: "uid='test_user_001' AND source='postLoan' AND execute_status='SUCCESS'"
          expected: "SUCCESS"
          timeout: 60
          interval: 3

# 用例2：幂等处理 - 相同serial_id，状态为SUCCESS，直接返回SUCCESS
- case_code: "TC_AI_copilot_ai_script_generate_002"
  case_name: "AI剧本信息实时生成_相同流水号已成功_幂等返回SUCCESS"
  element_code: "AI_copilot_ai_script_generate"
  element_name: "AI剧本信息实时生成"
  priority: "P1"
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
          where: "serial_id='test_serial_002'"
      
      - intent: "前置2：清理配置表数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_execute_config"
          where: "code='AI_SCRIPT_TEST_002'"
      
      - intent: "前置3：插入AI执行配置"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_execute_config"
          data:
            name: "测试AI剧本生成配置2"
            code: "AI_SCRIPT_TEST_002"
            type: "flow"
            agent_workflow_code: "25b65c76c7054f9785f303bc92d0c0b6"
            source: "postLoan"
      
      - intent: "前置4：插入已成功的记录"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          data:
            serial_id: "test_serial_002"
            uid: "test_user_002"
            queue: "ai_play_queue_test"
            ai_execute_code: "AI_SCRIPT_TEST_002"
            triger_scene: "REPAY_SUCCESS"
            input_data: "{\"uid\":\"test_user_002\",\"overdueCnt\":1,\"contents\":\"测试内容\"}"
            execute_status: "SUCCESS"
            output_data: "{\"character\":\"成功角色\",\"target\":\"本人\",\"resp_code\":\"1\",\"resp_msg\":\"success\"}"
            source: "postLoan"
    
    test_steps:
      - intent: "步骤1：使用相同serial_id再次调用接口"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          headers:
            Content-Type: "application/json"
          body:
            serial_id: "test_serial_002"
            uid: "test_user_002"
            source: "postLoan"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "AI_SCRIPT_TEST_002"
            queue: "ai_play_queue_test"
            inputData:
              contents: "重复调用内容"
        assertions:
          - intent: "断言1：校验API响应状态码"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 200
          
          - intent: "断言2：校验API响应中generateStatus为SUCCESS"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.generateStatus}"
              expected: "SUCCESS"
          
          - intent: "断言3：校验API响应中包含scriptContent"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.scriptContent.character}"
              expected: "成功角色"

# 用例3：幂等处理 - 相同serial_id，状态为FAILURE，重新处理返回PROCESSING
- case_code: "TC_AI_copilot_ai_script_generate_003"
  case_name: "AI剧本信息实时生成_相同流水号失败后重试_返回PROCESSING重新处理"
  element_code: "AI_copilot_ai_script_generate"
  element_name: "AI剧本信息实时生成"
  priority: "P1"
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
          where: "serial_id='test_serial_003'"
      
      - intent: "前置2：清理配置表数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_execute_config"
          where: "code='AI_SCRIPT_TEST_003'"
      
      - intent: "前置3：插入AI执行配置"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_execute_config"
          data:
            name: "测试AI剧本生成配置3"
            code: "AI_SCRIPT_TEST_003"
            type: "flow"
            agent_workflow_code: "25b65c76c7054f9785f303bc92d0c0b6"
            source: "postLoan"
      
      - intent: "前置4：插入失败状态的记录"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          data:
            serial_id: "test_serial_003"
            uid: "test_user_003"
            queue: "ai_play_queue_test"
            ai_execute_code: "AI_SCRIPT_TEST_003"
            triger_scene: "REPAY_SUCCESS"
            input_data: "{\"uid\":\"test_user_003\",\"overdueCnt\":1,\"contents\":\"测试内容\"}"
            execute_status: "FAILURE"
            failure_reason: "AI调用超时"
            source: "postLoan"
    
    test_steps:
      - intent: "步骤1：使用相同serial_id再次调用接口"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          headers:
            Content-Type: "application/json"
          body:
            serial_id: "test_serial_003"
            uid: "test_user_003"
            source: "postLoan"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "AI_SCRIPT_TEST_003"
            queue: "ai_play_queue_test"
            inputData:
              contents: "重试内容"
        assertions:
          - intent: "断言1：校验API响应状态码"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 200
          
          - intent: "断言2：校验API响应中generateStatus为PROCESSING"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.generateStatus}"
              expected: "PROCESSING"
          
          - intent: "断言3：校验数据库中记录状态已更新为PROCESSING"
            action: "assert_database_field"
            params:
              database: "copilot"
              table: "ai_script_recommendation_log"
              field: "execute_status"
              where: "serial_id='test_serial_003' AND execute_status='PROCESSING'"
              expected: "PROCESSING"

# 用例4：配置校验失败 - aiExecuteCode不存在
- case_code: "TC_AI_copilot_ai_script_generate_004"
  case_name: "AI剧本信息实时生成_不存在的AI执行编号_返回422错误"
  element_code: "AI_copilot_ai_script_generate"
  element_name: "AI剧本信息实时生成"
  priority: "P1"
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
          where: "uid='test_user_004'"
    
    test_steps:
      - intent: "步骤1：调用接口，使用不存在的aiExecuteCode"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          headers:
            Content-Type: "application/json"
          body:
            serial_id: "${uuid()}"
            uid: "test_user_004"
            source: "postLoan"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "NON_EXISTENT_CODE"
            queue: "ai_play_queue_test"
            inputData:
              contents: "测试内容"
        assertions:
          - intent: "断言1：校验API响应状态码为422"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 422
          
          - intent: "断言2：校验错误信息为'ai执行编号不存在'"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.message}"
              expected: "ai执行编号不存在"
          
          - intent: "断言3：校验数据库中没有插入新记录"
            action: "assert_database_record_count"
            params:
              database: "copilot"
              table: "ai_script_recommendation_log"
              where: "uid='test_user_004'"
              expected: 0

# 用例5：配置校验失败 - agent_workflow_code不匹配
- case_code: "TC_AI_copilot_ai_script_generate_005"
  case_name: "AI剧本信息实时生成_agent_workflow_code不匹配_返回422错误"
  element_code: "AI_copilot_ai_script_generate"
  element_name: "AI剧本信息实时生成"
  priority: "P1"
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
          where: "uid='test_user_005'"
      
      - intent: "前置2：清理配置表数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_execute_config"
          where: "code='AI_SCRIPT_INVALID_005'"
      
      - intent: "前置3：插入错误agent_workflow_code的配置"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_execute_config"
          data:
            name: "测试AI剧本生成配置5"
            code: "AI_SCRIPT_INVALID_005"
            type: "flow"
            agent_workflow_code: "WRONG_WORKFLOW_CODE"
            source: "postLoan"
    
    test_steps:
      - intent: "步骤1：调用接口，使用agent_workflow_code不匹配的配置"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          headers:
            Content-Type: "application/json"
          body:
            serial_id: "${uuid()}"
            uid: "test_user_005"
            source: "postLoan"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "AI_SCRIPT_INVALID_005"
            queue: "ai_play_queue_test"
            inputData:
              contents: "测试内容"
        assertions:
          - intent: "断言1：校验API响应状态码为422"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 422
          
          - intent: "断言2：校验错误信息为'ai执行编号不存在'"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.message}"
              expected: "ai执行编号不存在"
          
          - intent: "断言3：校验数据库中没有插入新记录"
            action: "assert_database_record_count"
            params:
              database: "copilot"
              table: "ai_script_recommendation_log"
              where: "uid='test_user_005'"
              expected: 0

# 用例6：基准获取失败 - 未找到uid+source的最新记录
- case_code: "TC_AI_copilot_ai_script_generate_006"
  case_name: "AI剧本信息实时生成_未找到离线数据_返回422错误"
  element_code: "AI_copilot_ai_script_generate"
  element_name: "AI剧本信息实时生成"
  priority: "P1"
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
          where: "uid='test_user_006' AND source='postLoan'"
      
      - intent: "前置2：清理配置表数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_execute_config"
          where: "code='AI_SCRIPT_TEST_006'"
      
      - intent: "前置3：插入AI执行配置"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_execute_config"
          data:
            name: "测试AI剧本生成配置6"
            code: "AI_SCRIPT_TEST_006"
            type: "flow"
            agent_workflow_code: "25b65c76c7054f9785f303bc92d0c0b6"
            source: "postLoan"
    
    test_steps:
      - intent: "步骤1：调用接口，该uid+source无历史记录"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          headers:
            Content-Type: "application/json"
          body:
            serial_id: "${uuid()}"
            uid: "test_user_006"
            source: "postLoan"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "AI_SCRIPT_TEST_006"
            queue: "ai_play_queue_test"
            inputData:
              contents: "测试内容"
        assertions:
          - intent: "断言1：校验API响应状态码为422"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 422
          
          - intent: "断言2：校验错误信息为'未找到离线数据'"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.message}"
              expected: "未找到离线数据"
          
          - intent: "断言3：校验数据库中没有插入新记录"
            action: "assert_database_record_count"
            params:
              database: "copilot"
              table: "ai_script_recommendation_log"
              where: "uid='test_user_006'"
              expected: 0
```