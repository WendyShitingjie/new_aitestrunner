
### JDBC 批量入仓 BPM 审批消息构造协议

- **传输层**:
    - **Queue**: `dataops.queue.receiveBatchOperationFlow`
    - **Cluster**: `amqp-cn-4591j61c6009`

- **消息体 (Payload) 结构**:
    - **外层字段清单**:
        1. `startUid`: 发起人 UID
        2. `orderNo`: BPM 工单号。
        3. `dataMap`: 业务载荷（需二次序列化的字符串）。
        4. `processInstId`: BPM 流程实例 ID。
        5. `operatorUid`: 审批人 UID。
        6. `operator`: 审批人姓名。
        7. `startName`: 发起人姓名。
        8. `status`: 审批状态（`STATUS_APPROVED` 或 `STATUS_REJECTED`）。
    
    - **内层 `dataMap` 字段清单**:
        1. `fileName`: 批量操作上传的文件名。
        2. `sceneType`: 场景路由枚举（详见下方字典）。
        3. `createdBy`: 任务创建人姓名。
        4. `batchTaskId`: 批量操作任务 ID（同 taskId）。
        5. `scOwnerUid`: 安全合规负责人 UID。
        6. `taskId`: 批量操作任务 ID。
        7. `recordCnt`: 上传文件中的记录总数。
        8. `scene`: 场景中文描述（详见下方字典）。
        9. `rejectReason`: 审批拒绝原因（**在 status 为 STATUS_REJECTED 时非必填**）。

    - **场景字典对照 (Routing Dictionary)**:
        | 业务动作 | `sceneType` (枚举值) | `scene` (中文说明) |
        | :--- | :--- | :--- |
        | 批量新增任务 | `jdbcInputBatchAddTask` | 批量新增任务 |
        | 批量新增字段 | `jdbcInputBatchAddField` | 批量新增字段 |
        | 批量修改任务 | `jdbcInputBatchModifyTask` | 批量修改任务 |
        | 批量下线任务 | `jdbcInputBatchOfflineTask` | 批量下线任务 |

- **取值逻辑**:
    - **`taskId` / `batchTaskId`**: 取自 `dataops_batch_operation_task` 表的 `id`（对应 `/dataops/etlx/batch/v2/validate` 接口返回的 `data.taskId`）。
    - **`orderNo`**: 取自 `dataops_bpm_record` 表的 `order_no` 字段。
    - **`processInstId`**: 取自 `dataops_bpm_record` 表的 `bpm_process_id` 字段。
    - **`fileName`**: 取自 `dataops_batch_operation_task.file_name`。
    - **`status`**: 
        *   审批通过：固定值 `STATUS_APPROVED`
        *   审批拒绝：固定值 `STATUS_REJECTED`
    - **`sceneType`**: 取自用户提供的自然语言，如JDBC批量入仓-新增任务就是`jdbcInputBatchAddTask`，对应的scene就是`批量新增任务`；详情参考上面的场景字典对照 (Routing Dictionary)
    - **`startUid`**: 默认 `71e8b23d-45e2-497a-b247-f5b807fb4f65`
    - **`startName`**: 默认 `施婷杰`
    - **`operatorUid`**: 默认 `6260e238-93c5-4324-8d0f-e3ba17659a14`
    - **`operator`**: 默认 `陈沈伟`
    - **`createdBy`**: 默认 `施婷杰`
    - **`scOwnerUid`**: 默认 `6260e238-93c5-4324-8d0f-e3ba17659a14`
    - **`rejectReason`**: 默认 `mq_sender_invoke_审批失败原因`
   
- **数据库查询连接信息以及sql**:

```sql
SELECT
    -- 消息体所需核心字段
    r.process_instance_node_id AS batchTaskId,
    r.process_instance_node_id AS taskId,
    r.bpm_process_id AS processInstId,
    r.order_no AS orderNo,
    t.file_name AS file_name
FROM
    dataops_bpm_record r
INNER JOIN
    dataops_batch_operation_task t 
    ON r.process_instance_node_id = t.id  -- 基础关联条件
WHERE
    r.process_key = 'bg_jdbc_rc_plxz_rw'  -- 确保1:1映射的核心过滤条件
    AND r.process_instance_node_id='{taskid}'
    AND r.status = 2;
```
#### 数据库连接查询信息如下
- **Host**: `bigdata-biz.db.ali-bj-bdsit01.shuheo.net`
- **Instance**: `bigdata-biz`
- **Database**: `dataops`
- **User**: `bdsit_user_0e0bc33`
- **Password**: `bdsit_user_0e0bc33_26587a`


- **验证 Check 点 (Checklist)**:
    1. **状态流转验证**: 
       *   若 `status` 为 `STATUS_APPROVED`：`dataops_batch_operation_task.task_status` 必须由 `PENDING_APPROVAL` 变更为 `EXECUTING` 或 `SUCCESS`。
       *   若 `status` 为 `STATUS_REJECTED`：`dataops_batch_operation_task.task_status` 必须由 `PENDING_APPROVAL` 变更为 `VALIDATE_FAILED`。
    2. **异常回写验证**: 
       *   在审批拒绝场景下，检查 `dataops_batch_operation_task` 表的 `error_message` 字段，应完整记录 `dataMap.rejectReason` 的内容。
    3. **工单状态验证**: 
       *   `dataops_bpm_record.status` 字段应同步更新为对应的审批结果。

---
**提示**: 使用 `mq-sender` 技能时，AI 只需组装标准的 `payload_dict` 对象（包含上述所有外层与内层字段），技能内部脚本会自动完成 `dataMap` 字段的 JSON 字符串化及转义处理。