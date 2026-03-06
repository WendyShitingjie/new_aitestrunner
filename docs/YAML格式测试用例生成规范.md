# YAML格式测试用例生成规范

## 📋 概述

本规范用于指导AI基于**MD格式测试用例集 + 知识库**生成YAML格式的可执行测试用例。YAML格式用例是测试用例的**第二层**，主要用于**自动化执行**，强调技术准确性和可执行性。

**核心原则**:
- ✅ 基于MD用例集 + 知识库生成
- ✅ 包含完整的技术实现细节
- ✅ 使用原语调用，可直接执行
- ✅ 包含详细的注释说明

---

## 🎯 设计理念

### 为什么使用YAML格式？

1. **可执行性**: 测试框架可以直接解析和执行
2. **结构化**: 清晰的层次结构，易于解析
3. **技术完整**: 包含所有技术实现细节（原语、参数、断言）
4. **可追溯**: 关联知识库，便于维护和更新

### YAML格式 vs MD格式

| 维度 | YAML格式（执行层） | MD格式（业务层） |
|------|-------------------|----------------|
| **目标用户** | 测试框架 | 业务人员、产品经理 |
| **内容** | 技术实现、原语调用 | 业务逻辑、测试目的 |
| **长度** | 不限（通常100-300行） | 100-150行 |
| **可读性** | ⭐⭐ 一般 | ⭐⭐⭐⭐⭐ 非常好 |
| **用途** | 自动化执行 | 评审、沟通 |

---

## 📝 文件结构规范

### 文件命名

**格式**: `TC_<业务流程ID>_<序号>_<用例名称>.yaml`

**示例**:
- `TC_TKF001_001_离线剧本批量生成_正常流程.yaml`
- `TC_TKF001_002_离线剧本批量生成_断点续传.yaml`

### 文件组织

**原则**: 一个MD用例 = 一个YAML文件

- ✅ 每个MD用例对应一个独立的YAML文件
- ✅ 文件名包含业务流程ID、序号、用例名称
- ✅ 存放在 `cases/` 目录

---

## 📄 YAML用例文件结构

### 完整结构

```yaml
# ============================================================================
# 测试用例：<用例名称>
# ============================================================================
# 知识来源: <关联的知识文档>
# 生成方式: AI基于Test Knowledge Tree自动生成
# 生成时间: YYYY-MM-DD
# ============================================================================

test_case_id: <用例ID>
test_name: <用例名称>
business_flow: <业务流程ID>
business_rules:
  - <业务规则ID>  # 注释说明

# 关联的知识文档
related_knowledge:
  flows:
    - <业务流程知识>
  rules:
    - <业务规则知识>
  data_components:
    - <数据组件知识>
  job_components:
    - <Job组件知识>
  integration_components:
    - <集成组件知识>

# 测试意图
test_intent:
  # ========== 前置条件（准备测试数据） ==========
  preconditions:
    - intent: "<前置条件说明>"
      primitive: <原语名称>
      params:
        <参数名>: <参数值>

  # ========== 测试步骤（黑盒视角） ==========
  test_steps:
    - intent: "<步骤说明>"
      primitive: <原语名称>
      params:
        <参数名>: <参数值>

      # 步骤的断言
      assertions:
        - intent: "<断言说明>"
          primitive: <断言原语名称>
          params:
            <参数名>: <参数值>

# 预期结果
expected_result:
  description: |
    <预期结果描述>
```

---

## 📐 各部分生成规范

### 1. 文件头部注释

**要求**:
- ✅ 包含用例名称
- ✅ 标注知识来源（关联的知识文档）
- ✅ 标注生成方式和时间
- ✅ 使用分隔线美化

**示例**:
```yaml
# ============================================================================
# 测试用例：离线剧本批量生成 - 正常流程（首次执行）
# ============================================================================
# 知识来源: TKF_001_离线剧本批量生成.md
# 生成方式: AI基于Test Knowledge Tree自动生成
# 生成时间: 2026-02-10
# ============================================================================
```

---

### 2. 基本信息

**要求**:
- ✅ test_case_id: 唯一标识，格式 `TC_<业务流程ID>_<序号>`
- ✅ test_name: 用例名称，格式 `<业务流程>_<场景>_<特征>`
- ✅ business_flow: 业务流程ID
- ✅ business_rules: 关联的业务规则列表（带注释）

**示例**:
```yaml
test_case_id: TC_TKF001_001
test_name: 离线剧本批量生成_正常流程_首次执行
business_flow: TKF_001
business_rules:
  - TKR_001  # DP数据产出状态判断
  - TKR_003  # 剧本生成状态判断
```

---

### 3. 关联知识文档

**要求**:
- ✅ 列出所有关联的知识文档
- ✅ 分类：flows、rules、data_components、job_components、integration_components
- ✅ 使用知识文档的完整ID

**示例**:
```yaml
related_knowledge:
  flows:
    - TKF_001_离线剧本批量生成
  rules:
    - TKR_001_DP数据产出状态判断
    - TKR_003_剧本生成状态判断
  data_components:
    - TKD_001_剧本推荐日志表
    - TKD_002_剧本推荐表
  job_components:
    - TKJ_001_AiScriptUidPullJob
  integration_components:
    - TKI_001_AI平台SDK集成
```

---

### 4. 前置条件 (preconditions)

**要求**:
- ✅ 每个前置条件包含：intent（意图说明）、primitive（原语名称）、params（参数）
- ✅ intent使用业务语言描述目的
- ✅ 添加注释说明知识来源和业务逻辑
- ✅ 按照执行顺序排列（先清理数据，再准备数据）

**示例**:
```yaml
preconditions:
  # 前置1: 清空历史数据（知识来源: TKD_001, TKD_002）
  - intent: "清空历史测试数据，确保测试环境干净"
    primitive: clean_test_data
    params:
      source: "postLoan"
      tables:
        - "copilot.ai_script_recommendation"
        - "copilot.ai_script_recommendation_log"

  # 前置2: 准备DataHub数据
  - intent: "准备DataHub的DP数据，batch_status=1表示数据已产出"
    primitive: prepare_datahub_data
    params:
      source: "postLoan"
      batch_status: "1"
      users:
        - customerName: "张三"
          age: "30"
```

---

### 5. 测试步骤 (test_steps)

**要求**:
- ✅ 每个步骤包含：intent、primitive、params、assertions
- ✅ intent描述步骤的业务目的
- ✅ 添加详细的注释说明（知识来源、业务逻辑、数据链路）
- ✅ assertions包含该步骤的所有断言

**示例**:
```yaml
test_steps:
  # ===== 步骤1: 触发阶段1（名单拉取Job）并验证执行结果 =====
  - intent: "触发离线剧本名单拉取定时任务并验证执行完成"
    primitive: trigger_scheduled_job
    params:
      job_name: "AiScriptUidPullJob"
      external_data:
        source: "postLoan"

    # 步骤1的预期结果断言（知识来源: TKD_004, TKD_001）
    # 数据链路: result_df → common_job_status (batch_no + source)
    assertions:
      - intent: "验证名单拉取Job执行成功（使用超时轮询）"
        primitive: assert_field_equals
        params:
          table: "copilot.common_job_status"
          field: "status"
          where: "job_name='AiScriptUidPullJob' AND business_type='postLoan' ORDER BY id DESC LIMIT 1"
          expected: "SUCCESS"
          timeout: 30
          poll_interval: 2
```

---

### 6. 断言 (assertions)

**要求**:
- ✅ 每个断言包含：intent、primitive、params
- ✅ intent描述断言的验证目的
- ✅ 使用合适的断言原语（assert_field_equals、assert_record_count等）
- ✅ 添加timeout和poll_interval参数（异步操作）
- ✅ 添加注释说明验证逻辑

**常用断言原语**:
- `assert_field_equals`: 验证字段值等于预期值
- `assert_record_count`: 验证记录数量
- `assert_all_records_match`: 验证所有记录的字段值都匹配
- `assert_all_json_fields_not_null`: 验证JSON字段非空

**示例**:
```yaml
assertions:
  - intent: "验证日志表插入了2条记录（使用超时轮询）"
    primitive: assert_record_count
    params:
      table: "copilot.ai_script_recommendation_log"
      where: "source='postLoan'"
      expected: 2
      timeout: 30  # 最大等待30秒
      poll_interval: 3  # 每3秒查询一次
    # 说明: Job执行是异步的，需要等待约1-2分钟

  - intent: "验证AI平台返回的character字段非空"
    primitive: assert_all_json_fields_not_null
    params:
      table: "copilot.ai_script_recommendation_log"
      json_field: "output_data"
      extract_fields: ["$.character"]
      where: "source='postLoan'"
```

---

### 7. 预期结果 (expected_result)

**要求**:
- ✅ 使用description字段描述整体预期结果
- ✅ 使用多行字符串（|）格式
- ✅ 列出所有关键验证点
- ✅ 使用业务语言描述

**示例**:
```yaml
expected_result:
  description: |
    1. 名单拉取Job执行成功，状态为SUCCESS
    2. 日志表插入2条记录，状态都为SUCCESS
    3. 剧本表插入2条记录
    4. 每条剧本都包含角色(character)、对象(target)、策略(pressure_points)
    5. AI平台调用成功，resp_code都为1
```

---

## 🔧 参数使用规范

### 1. 变量引用

**格式**: `${context.变量名}`

**用途**: 引用前面步骤保存到上下文中的变量

**示例**:
```yaml
params:
  batch_no: "${context.batch_no}"  # 引用前面步骤生成的batch_no
  uid: "${context.uids[0]}"  # 引用数组中的第一个uid
```

---

### 2. 函数调用

**格式**: `${函数名()}`

**常用函数**:
- `${uuid()}`: 生成UUID
- `${batch_no()}`: 生成批次号（yyyyMMdd001格式）
- `${serial_id()}`: 生成序列ID
- `${timestamp()}`: 生成时间戳

**示例**:
```yaml
params:
  uid: "${uuid()}"  # 自动生成UUID
  batch_no: "${batch_no()}"  # 自动生成批次号
  serial_id: "${serial_id()}"  # 自动生成序列ID
```

---

### 3. 字符串拼接

**格式**: `"前缀_${变量}_后缀"`

**示例**:
```yaml
params:
  job_name: "AiScript_${context.type}_Job"
```

---

## 📝 注释规范

### 1. 分隔注释

**用途**: 分隔不同的逻辑块

**格式**:
```yaml
# ========== 前置条件（准备测试数据） ==========
# ===== 步骤1: 触发阶段1（名单拉取Job）并验证执行结果 =====
```

---

### 2. 说明注释

**用途**: 解释业务逻辑、数据链路、注意事项

**格式**:
```yaml
# 前置1: 清空历史数据（知识来源: TKD_001, TKD_002）
# 说明: 必须按照从下游到上游的顺序清理，避免外键约束错误

# 数据链路: result_df → common_job_status (batch_no + source)
#          base_df → recommendation_log (queue + ai_execute_code + source)

# 字段映射: common_job_status.business_type = 其他表.source
```

---

### 3. 行内注释

**用途**: 解释参数含义

**格式**:
```yaml
params:
  timeout: 30  # 最大等待30秒
  poll_interval: 2  # 每2秒查询一次
  batch_status: "1"  # DP数据已产出
```

---



## ✅ 生成检查清单

### 结构检查

- [ ] 文件头部包含完整注释（用例名称、知识来源、生成方式、生成时间）
- [ ] 包含基本信息（test_case_id、test_name、business_flow、business_rules）
- [ ] 包含关联知识文档（flows、rules、data_components等）
- [ ] 包含test_intent（preconditions、test_steps）
- [ ] 包含expected_result

### 内容检查

- [ ] 每个前置条件包含intent、primitive、params
- [ ] 每个测试步骤包含intent、primitive、params、assertions
- [ ] 每个断言包含intent、primitive、params
- [ ] 异步操作的断言包含timeout和poll_interval参数
- [ ] 所有原语名称正确（参考原语文档）

### 注释检查

- [ ] 前置条件有注释说明知识来源和业务逻辑
- [ ] 测试步骤有注释说明数据链路和字段映射
- [ ] 断言有注释说明验证逻辑
- [ ] 复杂参数有行内注释

### 参数检查

- [ ] 变量引用格式正确（${context.变量名}）
- [ ] 函数调用格式正确（${函数名()}）
- [ ] 数组索引格式正确（${context.uids[0]}）
- [ ] 字符串拼接格式正确

---

## 📚 参考示例

完整示例请参考：
- `cases/TC_TKF001_001_离线剧本批量生成_正常流程.yaml`
- `cases/TC_TKF001_002_离线剧本批量生成_断点续传.yaml`
- `cases/TC_TKF001_003_离线剧本批量生成_失败重试.yaml`

---

## 🔄 生成流程

### 输入

1. **MD格式测试用例集**: 包含业务逻辑和测试目的
2. **知识库**: 包含业务流程、业务规则、数据组件、Job组件等

### 处理步骤

1. **解析MD用例**: 提取测试目的、测试数据、测试步骤、预期结果
2. **查询知识库**: 根据业务流程ID查询相关知识
3. **映射原语**: 将业务步骤映射到具体的原语调用
4. **生成参数**: 根据知识库生成原语参数
5. **生成断言**: 根据预期结果生成断言
6. **添加注释**: 添加知识来源、业务逻辑、数据链路等注释

### 输出

- 完整的YAML格式测试用例文件
- 可直接被测试框架执行

---

## 💡 最佳实践

### 1. 注释要充分

- ✅ 每个前置条件都要注释知识来源
- ✅ 每个测试步骤都要注释数据链路
- ✅ 每个断言都要注释验证逻辑
- ✅ 复杂参数都要有行内注释

### 2. 断言要完整

- ✅ 验证Job执行状态
- ✅ 验证数据库记录数量
- ✅ 验证数据库字段值
- ✅ 验证JSON字段非空
- ✅ 使用超时轮询机制（异步操作）

### 3. 参数要准确

- ✅ 使用变量引用避免硬编码
- ✅ 使用函数生成动态值
- ✅ 参数值要符合知识库定义
- ✅ 表名、字段名要准确

### 4. 结构要清晰

- ✅ 使用分隔注释分隔逻辑块
- ✅ 前置条件按执行顺序排列
- ✅ 测试步骤按业务流程排列
- ✅ 断言按验证维度分组

---

## 🚫 常见错误

### 1. 缺少超时参数

**错误**:
```yaml
- intent: "验证Job执行成功"
  primitive: assert_field_equals
  params:
    table: "copilot.common_job_status"
    field: "status"
    expected: "SUCCESS"
```

**正确**:
```yaml
- intent: "验证Job执行成功（使用超时轮询）"
  primitive: assert_field_equals
  params:
    table: "copilot.common_job_status"
    field: "status"
    expected: "SUCCESS"
    timeout: 30  # 添加超时参数
    poll_interval: 2  # 添加轮询间隔
```

---

### 2. 硬编码批次号

**错误**:
```yaml
params:
  batch_no: "20260210001"  # 硬编码
```

**正确**:
```yaml
params:
  batch_no: "${context.batch_no}"  # 使用变量引用
  # 或
  batch_no: "${batch_no()}"  # 使用函数生成
```

---

### 3. 缺少注释

**错误**:
```yaml
preconditions:
  - intent: "清空历史测试数据"
    primitive: clean_test_data
    params:
      source: "postLoan"
```

**正确**:
```yaml
preconditions:
  # 前置1: 清空历史数据（知识来源: TKD_001, TKD_002）
  # 说明: 必须按照从下游到上游的顺序清理，避免外键约束错误
  - intent: "清空历史测试数据，确保测试环境干净"
    primitive: clean_test_data
    params:
      source: "postLoan"
      tables:  # 按依赖顺序清理
        - "copilot.ai_script_recommendation"
        - "copilot.ai_script_recommendation_log"
```

---

### 4. WHERE条件不准确

**错误**:
```yaml
params:
  where: "job_name='AiScriptUidPullJob'"  # 缺少排序和限制
```

**正确**:
```yaml
params:
  where: "job_name='AiScriptUidPullJob' AND business_type='postLoan' ORDER BY id DESC LIMIT 1"
  # 说明: 使用ORDER BY id DESC LIMIT 1获取最新记录
```

---

**规范版本**: v1.0
**创建日期**: 2026-02-10
**维护人员**: AI测试团队
