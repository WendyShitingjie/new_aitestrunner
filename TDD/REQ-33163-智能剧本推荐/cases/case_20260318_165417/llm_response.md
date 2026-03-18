<thinking>
1. DDL分析：
   - AD_copilot_ai_script_recommendation_log表：主键为id(AUTO_INCREMENT)，唯一键为uk_serial_id(serial_id)，非空字段包含：serial_id, uid, triger_scene, execute_status, source
   - AD_copilot_ai_execute_config表：主键为id(AUTO_INCREMENT)，索引为idx_code(code)
   - AD_copilot_ai_script_recommendation表：主键为id(AUTO_INCREMENT)，唯一键为uk_uid_source(uid,source)

2. 场景拆解：根据AI_copilot_ai_script_generate的logic_rules，需要覆盖：
   - 正向流程：合法参数->返回PROCESSING->异步成功
   - 配置校验失败：aiExecuteCode不存在
   - 基准数据获取失败：uid+source无历史记录
   - 幂等处理：相同serial_id不同状态

3. 数据清理与构造：根据业务规则，需要先清理serial_id相关的数据，然后构造AI执行配置和基准数据

4. 上下文变量追踪：前置构造的serial_id将通过${context.data.serial_id}传递给API调用步骤
</thinking>

```yaml
- case_code: "TC_AI_copilot_ai_script_generate_001"
  case_name: "AI剧本信息实时生成_合法参数入参_返回PROCESSING状态"
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
      - intent: "前置1：清理历史测试数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          where: "serial_id='test_serial_001' OR uid='test_uid_001'"
          
      - intent: "前置2：清理配置表数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_execute_config"
          where: "code='TEST_SCRIPT_GEN_001'"
          
      - intent: "前置3：插入AI执行配置"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_execute_config"
          data:
            name: "测试剧本生成配置"
            code: "TEST_SCRIPT_GEN_001"
            type: "flow"
            agent_workflow_code: "25b65c76c7054f9785f303bc92d0c0b6"
            source: "postLoan"
            
      - intent: "前置4：插入基准数据"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          data:
            serial_id: "base_serial_001"
            uid: "test_uid_001"
            queue: "test_queue"
            ai_execute_code: "TEST_SCRIPT_GEN_001"
            triger_scene: "REPAY_SUCCESS"
            input_data: "{\"uid\":\"test_uid_001\",\"overdueCnt\":2,\"contents\":\"基准测试内容\"}"
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
            uid: "test_uid_001"
            source: "postLoan"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "TEST_SCRIPT_GEN_001"
            queue: "test_queue"
            inputData:
              contents: "新的工单内容：用户进线，咨询逾期账单费用减免"
            featureComputeRequest:
              bizSerial: "${uuid()}"
              uid: "test_uid_001"
              commonParams:
                uid: "test_uid_001"
              featureConfigs:
                - featureKey: "rt_usr_adt_rat_csh"
                  alias: "overdueCnt"
        assertions:
          - intent: "断言1：校验API响应状态码"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 200
          - intent: "断言2：校验API响应生成状态为PROCESSING"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.generateStatus}"
              expected: "PROCESSING"
          - intent: "断言3：校验API响应流水号正确"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.serialId}"
              expected: "test_serial_001"
          - intent: "断言4：校验数据库中记录已插入PROCESSING状态"
            action: "assert_database_field"
            params:
              database: "copilot"
              table: "ai_script_recommendation_log"
              field: "execute_status"
              where: "serial_id='test_serial_001'"
              expected: "PROCESSING"
              timeout: 30

- case_code: "TC_AI_copilot_ai_script_generate_002"
  case_name: "AI剧本信息实时生成_配置校验失败_返回422错误"
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
      - intent: "前置1：清理历史测试数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          where: "serial_id='test_serial_002' OR uid='test_uid_002'"
          
      - intent: "前置2：清理配置表数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_execute_config"
          where: "code='INVALID_CODE_001'"
    
    test_steps:
      - intent: "步骤1：调用AI剧本生成接口-使用不存在的配置编码"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          body:
            serial_id: "test_serial_002"
            uid: "test_uid_002"
            source: "postLoan"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "INVALID_CODE_001"
            queue: "test_queue"
        assertions:
          - intent: "断言1：校验API响应状态码为422"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 422
          - intent: "断言2：校验API响应错误信息"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.message}"
              expected: "ai执行编号不存在"
          - intent: "断言3：校验数据库中无新记录插入"
            action: "assert_database_record_count"
            params:
              database: "copilot"
              table: "ai_script_recommendation_log"
              where: "serial_id='test_serial_002'"
              expected: 0

- case_code: "TC_AI_copilot_ai_script_generate_003"
  case_name: "AI剧本信息实时生成_基准数据获取失败_返回422错误"
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
      - intent: "前置1：清理历史测试数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          where: "serial_id='test_serial_003' OR uid='test_uid_003'"
          
      - intent: "前置2：清理配置表数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_execute_config"
          where: "code='TEST_SCRIPT_GEN_003'"
          
      - intent: "前置3：插入有效的AI执行配置"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_execute_config"
          data:
            name: "测试剧本生成配置"
            code: "TEST_SCRIPT_GEN_003"
            type: "flow"
            agent_workflow_code: "25b65c76c7054f9785f303bc92d0c0b6"
            source: "postLoan"
    
    test_steps:
      - intent: "步骤1：调用AI剧本生成接口-用户无历史基准数据"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          body:
            serial_id: "test_serial_003"
            uid: "test_uid_003"
            source: "postLoan"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "TEST_SCRIPT_GEN_003"
            queue: "test_queue"
        assertions:
          - intent: "断言1：校验API响应状态码为422"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 422
          - intent: "断言2：校验API响应错误信息"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.message}"
              expected: "未找到离线数据"
          - intent: "断言3：校验数据库中无新记录插入"
            action: "assert_database_record_count"
            params:
              database: "copilot"
              table: "ai_script_recommendation_log"
              where: "serial_id='test_serial_003'"
              expected: 0

- case_code: "TC_AI_copilot_ai_script_generate_004"
  case_name: "AI剧本信息实时生成_幂等处理成功状态_返回SUCCESS结果"
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
      - intent: "前置1：清理历史测试数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          where: "serial_id='idempotent_serial_004' OR uid='test_uid_004'"
          
      - intent: "前置2：清理配置表数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_execute_config"
          where: "code='TEST_SCRIPT_GEN_004'"
          
      - intent: "前置3：插入AI执行配置"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_execute_config"
          data:
            name: "测试剧本生成配置"
            code: "TEST_SCRIPT_GEN_004"
            type: "flow"
            agent_workflow_code: "25b65c76c7054f9785f303bc92d0c0b6"
            source: "postLoan"
            
      - intent: "前置4：插入已成功的幂等记录"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          data:
            serial_id: "idempotent_serial_004"
            uid: "test_uid_004"
            queue: "test_queue"
            ai_execute_code: "TEST_SCRIPT_GEN_004"
            triger_scene: "REPAY_SUCCESS"
            input_data: "{\"uid\":\"test_uid_004\",\"contents\":\"测试内容\"}"
            output_data: "{\"character\":\"还呗财务部\",\"target\":\"本人\",\"pressure_points\":[{\"point\":\"施压点1\",\"script\":[\"话术11\",\"话术12\"]}],\"resp_code\":\"1\",\"resp_msg\":\"success\"}"
            execute_status: "SUCCESS"
            source: "postLoan"
    
    test_steps:
      - intent: "步骤1：再次调用AI剧本生成接口-相同serial_id"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          body:
            serial_id: "idempotent_serial_004"
            uid: "test_uid_004"
            source: "postLoan"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "TEST_SCRIPT_GEN_004"
            queue: "test_queue"
        assertions:
          - intent: "断言1：校验API响应状态码"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 200
          - intent: "断言2：校验API响应生成状态为SUCCESS"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.generateStatus}"
              expected: "SUCCESS"
          - intent: "断言3：校验API响应包含剧本内容"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.scriptContent.character}"
              expected: "还呗财务部"
          - intent: "断言4：校验数据库记录状态仍为SUCCESS"
            action: "assert_database_field"
            params:
              database: "copilot"
              table: "ai_script_recommendation_log"
              field: "execute_status"
              where: "serial_id='idempotent_serial_004'"
              expected: "SUCCESS"

- case_code: "TC_AI_copilot_ai_script_generate_005"
  case_name: "AI剧本信息实时生成_幂等处理失败状态_重新触发处理"
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
      - intent: "前置1：清理历史测试数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          where: "serial_id='idempotent_fail_005' OR uid='test_uid_005'"
          
      - intent: "前置2：清理配置表数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_execute_config"
          where: "code='TEST_SCRIPT_GEN_005'"
          
      - intent: "前置3：插入AI执行配置"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_execute_config"
          data:
            name: "测试剧本生成配置"
            code: "TEST_SCRIPT_GEN_005"
            type: "flow"
            agent_workflow_code: "25b65c76c7054f9785f303bc92d0c0b6"
            source: "postLoan"
            
      - intent: "前置4：插入失败的幂等记录"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          data:
            serial_id: "idempotent_fail_005"
            uid: "test_uid_005"
            queue: "test_queue"
            ai_execute_code: "TEST_SCRIPT_GEN_005"
            triger_scene: "REPAY_SUCCESS"
            input_data: "{\"uid\":\"test_uid_005\",\"contents\":\"测试内容\"}"
            execute_status: "FAILURE"
            failure_reason: "AI平台调用超时"
            source: "postLoan"
    
    test_steps:
      - intent: "步骤1：再次调用AI剧本生成接口-相同serial_id但之前失败"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          body:
            serial_id: "idempotent_fail_005"
            uid: "test_uid_005"
            source: "postLoan"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "TEST_SCRIPT_GEN_005"
            queue: "test_queue"
        assertions:
          - intent: "断言1：校验API响应状态码"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 200
          - intent: "断言2：校验API响应生成状态为PROCESSING"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.generateStatus}"
              expected: "PROCESSING"
          - intent: "断言3：校验数据库记录状态已更新为PROCESSING"
            action: "assert_database_field"
            params:
              database: "copilot"
              table: "ai_script_recommendation_log"
              field: "execute_status"
              where: "serial_id='idempotent_fail_005'"
              expected: "PROCESSING"
              timeout: 10
```