<thinking>
1. DDL分析：
   - AD_copilot_ai_script_recommendation_log表：主键id(自增)，唯一键uk_serial_id(serial_id)，非空字段包括serial_id, uid, triger_scene, execute_status, source
   - AD_copilot_ai_execute_config表：主键id(自增)，索引idx_code(code)
   - AD_copilot_ai_script_recommendation表：主键id(自增)，唯一键uk_uid_source(uid,source)

2. 场景拆解：
   - 正向场景：合法参数，存在基准数据，配置校验通过，返回PROCESSING
   - 异常场景：aiExecuteCode不存在、未找到离线数据、幂等处理等

3. 业务规则：
   - 幂等处理：相同serial_id的处理逻辑
   - 配置校验：aiExecuteCode必须在配置表中且agent_workflow_code=25b65c76c7054f9785f303bc92d0c0b6
   - 基准获取：从log表获取uid+source最新记录的input_data
   - 异步处理：插入PROCESSING记录后立即返回

4. 数据清理与构造：需要先清理相关表的历史数据，然后构造基础数据
</thinking>

```yaml
- case_code: "TC_AI_copilot_ai_script_generate_001"
  case_name: "AI剧本信息实时生成_合法数据入参_返回PROCESSING"
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
      - intent: "前置1：清理历史数据-清理log表"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          where: "uid='test_user_001' AND source='autotest2'"
          
      - intent: "前置2：清理历史数据-清理配置表"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_execute_config"
          where: "code='AI_SCRIPT_RECOMMANDATION_2'"
          
      - intent: "前置3：清理历史数据-清理推荐表"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_script_recommendation"
          where: "uid='test_user_001' AND source='autotest2'"
          
      - intent: "前置4：构造配置表数据"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_execute_config"
          data:
            name: "AI剧本生成配置"
            code: "AI_SCRIPT_RECOMMANDATION_2"
            type: "flow"
            agent_workflow_code: "25b65c76c7054f9785f303bc92d0c0b6"
            source: "postLoan"
            
      - intent: "前置5：构造基准数据-在log表中插入基准记录"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          data:
            serial_id: "${uuid()}"
            uid: "test_user_001"
            queue: "ai_play_queue_22"
            ai_execute_code: "AI_SCRIPT_RECOMMANDATION_2"
            triger_scene: "REPAY_SUCCESS"
            input_data: "{\"uid\":\"test_user_001\",\"overdueCnt\":1,\"contents\":\"原始内容\"}"
            execute_status: "SUCCESS"
            source: "autotest2"
    
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
            source: "autotest2"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "AI_SCRIPT_RECOMMANDATION_2"
            queue: "ai_play_queue"
            inputData:
              contents: "工单内容：用户进线，咨询逾期账单费用减免，辛苦处理。 工单处理：沟通中无故挂断，告知没有政策帮助，五点主动处理完成?"
            featureComputeRequest:
              bizSerial: "${uuid()}"
              uid: "test_user_001"
              commonParams:
                uid: "test_user_001"
                caseNumber: "case14933_200000012"
              featureConfigs:
                - featureKey: "rt_usr_adt_rat_csh"
                  alias: "overdueCnt"
        assertions:
          - intent: "断言1：校验API响应状态码为200"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 200
              
          - intent: "断言2：校验API响应状态为PROCESSING"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.generateStatus}"
              expected: "PROCESSING"
              
          - intent: "断言3：校验数据库中记录状态为PROCESSING"
            action: "assert_database_field"
            params:
              database: "copilot"
              table: "ai_script_recommendation_log"
              field: "execute_status"
              where: "uid='test_user_001' AND source='autotest2'"
              expected: "PROCESSING"
              operator: "等于"
              timeout: 30
              interval: 2

- case_code: "TC_AI_copilot_ai_script_generate_002"
  case_name: "AI剧本信息实时生成_ai执行编号不存在_返回422"
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
      - intent: "前置1：清理配置表中相关数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_execute_config"
          where: "code='INVALID_CODE'"
    
    test_steps:
      - intent: "步骤1：调用AI剧本生成接口-使用不存在的执行编号"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          headers:
            Content-Type: "application/json"
          body:
            serial_id: "${uuid()}"
            uid: "test_user_002"
            source: "autotest2"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "INVALID_CODE"
            queue: "ai_play_queue"
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

- case_code: "TC_AI_copilot_ai_script_generate_003"
  case_name: "AI剧本信息实时生成_未找到离线数据_返回422"
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
      - intent: "前置1：清理log表中相关数据"
        action: "database_delete"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          where: "uid='test_user_003' AND source='autotest2'"
          
      - intent: "前置2：构造有效的配置数据"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_execute_config"
          data:
            name: "AI剧本生成配置"
            code: "AI_SCRIPT_RECOMMANDATION_3"
            type: "flow"
            agent_workflow_code: "25b65c76c7054f9785f303bc92d0c0b6"
            source: "postLoan"
    
    test_steps:
      - intent: "步骤1：调用AI剧本生成接口-用户无历史数据"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          headers:
            Content-Type: "application/json"
          body:
            serial_id: "${uuid()}"
            uid: "test_user_003"
            source: "autotest2"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "AI_SCRIPT_RECOMMANDATION_3"
            queue: "ai_play_queue"
        assertions:
          - intent: "断言1：校验API响应状态码为422"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 422
              
          - intent: "断言2：校验API响应错误信息为未找到离线数据"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.message}"
              expected: "未找到离线数据"

- case_code: "TC_AI_copilot_ai_script_generate_004"
  case_name: "AI剧本信息实时生成_幂等处理命中SUCCESS_返回SUCCESS"
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
          where: "serial_id='test_serial_004'"
          
      - intent: "前置2：构造配置数据"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_execute_config"
          data:
            name: "AI剧本生成配置"
            code: "AI_SCRIPT_RECOMMANDATION_4"
            type: "flow"
            agent_workflow_code: "25b65c76c7054f9785f303bc92d0c0b6"
            source: "postLoan"
            
      - intent: "前置3：构造已成功的记录"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          data:
            serial_id: "test_serial_004"
            uid: "test_user_004"
            queue: "ai_play_queue_22"
            ai_execute_code: "AI_SCRIPT_RECOMMANDATION_4"
            triger_scene: "REPAY_SUCCESS"
            input_data: "{\"uid\":\"test_user_004\",\"overdueCnt\":1,\"contents\":\"原始内容\"}"
            output_data: "{\"character\":\"还呗财务部\",\"target\":\"本人\",\"pressure_points\":[{\"point\":\"施压点1\",\"script\":[\"话术11\",\"话术12\"]}],\"resp_code\":\"1\",\"resp_msg\":\"success\"}"
            execute_status: "SUCCESS"
            source: "autotest2"
    
    test_steps:
      - intent: "步骤1：使用相同serial_id再次调用AI剧本生成接口"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          headers:
            Content-Type: "application/json"
          body:
            serial_id: "test_serial_004"
            uid: "test_user_004"
            source: "autotest2"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "AI_SCRIPT_RECOMMANDATION_4"
            queue: "ai_play_queue"
        assertions:
          - intent: "断言1：校验API响应状态码为200"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 200
              
          - intent: "断言2：校验API响应状态为SUCCESS"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.generateStatus}"
              expected: "SUCCESS"
              
          - intent: "断言3：校验API响应包含剧本内容"
            action: "assert_value"
            params:
              actual: "${context.http_response.body.scriptContent.character}"
              expected: "还呗财务部"

- case_code: "TC_AI_copilot_ai_script_generate_005"
  case_name: "AI剧本信息实时生成_幂等处理命中FAILURE_返回PROCESSING"
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
          where: "serial_id='test_serial_005'"
          
      - intent: "前置2：构造配置数据"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_execute_config"
          data:
            name: "AI剧本生成配置"
            code: "AI_SCRIPT_RECOMMANDATION_5"
            type: "flow"
            agent_workflow_code: "25b65c76c7054f9785f303bc92d0c0b6"
            source: "postLoan"
            
      - intent: "前置3：构造失败的记录"
        action: "database_insert"
        params:
          database: "copilot"
          table: "ai_script_recommendation_log"
          data:
            serial_id: "test_serial_005"
            uid: "test_user_005"
            queue: "ai_play_queue_22"
            ai_execute_code: "AI_SCRIPT_RECOMMANDATION_5"
            triger_scene: "REPAY_SUCCESS"
            input_data: "{\"uid\":\"test_user_005\",\"overdueCnt\":1,\"contents\":\"原始内容\"}"
            output_data: ""
            execute_status: "FAILURE"
            failure_reason: "AI平台调用失败"
            source: "autotest2"
    
    test_steps:
      - intent: "步骤1：使用相同serial_id再次调用AI剧本生成接口"
        action: "call_http_api"
        params:
          application: "copilot"
          endpoint: "/copilot/ai/script/generate"
          method: "POST"
          headers:
            Content-Type: "application/json"
          body:
            serial_id: "test_serial_005"
            uid: "test_user_005"
            source: "autotest2"
            triger_scene: "REPAY_SUCCESS"
            aiExecuteCode: "AI_SCRIPT_RECOMMANDATION_5"
            queue: "ai_play_queue"
        assertions:
          - intent: "断言1：校验API响应状态码为200"
            action: "assert_value"
            params:
              actual: "${context.http_response.status_code}"
              expected: 200
              
          - intent: "断言2：校验API响应状态为PROCESSING"
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
              where: "serial_id='test_serial_005'"
              expected: "PROCESSING"
              operator: "等于"
              timeout: 30
              interval: 2
```