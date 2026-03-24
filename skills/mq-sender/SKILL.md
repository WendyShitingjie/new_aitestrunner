---
name: mq-sender
displayName: 通用 MQ 发信机
description: 通过 mqplus 统一网关向不同业务队列投递消息，支持自动化双重序列化，配合业务构造协议 MD 实现全场景覆盖
---

# Skill: 通用 MQ 发信机 (mq-sender)

## 技能定义
该技能通过 mqplus 统一网关向不同业务队列投递消息。核心优势是具备”自动化双重序列化”能力，调用者无需手动处理 JSON 转义字符。

## 适用场景
当用户使用自然语言描述 MQ 消息发送需求时，自动触发此 skill：
- **JDBC 批量入仓审批消息**（必须明确具体操作类型）：
  - 批量新增任务审批（通过/拒绝）
  - 批量新增字段审批（通过/拒绝）
  - 批量修改任务审批（通过/拒绝）
  - 批量下线任务审批（通过/拒绝）
- 发送其他业务 MQ 消息
- 关键词：发送消息、审批通过、审批拒绝、MQ、消息队列

**重要提示**：JDBC 批量入仓场景必须提供 `taskId`（批量操作任务ID）

## AI 执行指令

### 执行原则
- **静默执行**：不展示中间查询过程和详细步骤，直接给用户最终结果
- **优先使用默认值**：协议 MD 中定义的默认值优先使用，不需要询问用户
- **自动化程度高**：能自动完成的步骤都自动完成

### 执行流程

#### 0. 验证必需参数
在执行前先验证关键参数：
- **JDBC 批量入仓场景的必需参数**：
  - `taskId`（批量操作任务ID）：必须由用户明确提供
  - 如果用户未提供，**立即中断执行**并提醒：
    ```
    ⚠️ 缺少必需参数：taskId

    JDBC 批量入仓操作需要提供批量任务ID（taskId）。
    您可以通过以下方式获取：
    1. 从批量操作任务表 dataops_batch_operation_task 查询
    2. 从 /dataops/etlx/batch/v2/validate 接口返回的 data.taskId

    请提供 taskId 后重试。
    ```
- **其他业务场景**：根据对应协议 MD 中的必需参数要求验证

#### 1. 识别业务场景
从用户的自然语言输入中识别业务场景和具体操作类型：
- **JDBC 批量入仓**：必须同时识别出具体操作类型
  - 批量新增任务：关键词”批量”+”新增任务”
  - 批量新增字段：关键词”批量”+”新增字段”
  - 批量修改任务：关键词”批量”+”修改任务”
  - 批量下线任务：关键词”批量”+”下线任务”
  - 如果用户只说”JDBC批量入仓审批”而未明确具体类型，**必须询问用户**明确是哪种操作
- **其他业务**：根据用户描述识别

#### 2. 定位协议 MD
根据识别的业务场景，在 `references/` 目录下找到对应的构造协议 MD：
- 使用 Glob 或 Read 工具查找匹配的 MD 文件
- 示例：JDBC 批量入仓 → `references/JDBC批量入仓_新增任务审批_消息构造协议.md`

#### 3. 读取并理解协议
读取协议 MD，提取关键信息：
- **传输层配置**：`cluster_name`、`queue`
- **消息体结构**：外层字段、内层字段（如 dataMap）
- **取值逻辑**：哪些字段需要查询数据库、SQL 语句、默认值
- **数据库连接信息**：host、port、database、user、password

#### 4. 查询数据库（如需要）
如果协议要求从数据库查询数据：
- 使用协议中提供的 SQL 和连接信息
- 直接在 Bash 中执行 Python 代码查询（不创建临时文件）
- 示例：
```python
python3 << 'EOF'
import pymysql
import json
# ... 查询逻辑
EOF
```

#### 5. 构造消息体
根据协议要求构造完整的 `payload_dict`：
- 使用查询到的数据库数据
- 使用协议中的默认值
- 使用用户提供的参数
- **注意**：嵌套字段（如 dataMap）只需提供对象/字典，脚本会自动序列化

#### 6. 调用发送脚本
调用 `scripts/mq_sender.py` 发送消息：
```bash
cd /path/to/skills/mq_sender/scripts && python3 mq_sender.py '{
  “cluster_name”: “xxx”,
  “queue”: “xxx”,
  “payload_dict”: {...},
  “reason”: “描述性原因”
}'
```

#### 7. 返回结果
简洁地告知用户执行结果：
- ✅ 成功：显示关键信息（taskId、工单号、状态等）
- ❌ 失败：显示错误原因

## 参数格式示例
调用 `mq_sender.py` 时的参数格式：
```json
{
  "cluster_name": "amqp-cn-4591j61c6009",
  "queue": "dataops.queue.receiveBatchOperationFlow",
  "payload_dict": {
    "orderNo": "xxx",
    "status": "STATUS_APPROVED",
    "dataMap": {
      "taskId": 123,  // ⚠️ JDBC批量入仓场景：必需参数，用户必须提供
      "fileName": "test.xlsx",
      "sceneType": "jdbcInputBatchAddTask"
    }
  },
  "reason": "Claude-Code-批量新增任务审批通过"
}
```

## 扩展新业务场景
添加新业务只需在 `references/` 目录下创建新的构造协议 MD，包含：
1. 传输层配置（Queue、Cluster）
2. 消息体结构（外层字段、内层字段）
3. 取值逻辑（数据库查询 SQL、默认值）
4. 数据库连接信息（如需要）

AI 会自动读取并按照新协议执行。