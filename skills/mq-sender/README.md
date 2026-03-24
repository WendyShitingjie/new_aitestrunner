# MQ-Sender 通用技能工具箱

## 1. 简介
本工具旨在解决测试环境中模拟异步回调（如 BPM 审批、任务状态同步）造数难的问题。通过一个通用的发送脚本，配合不同的”业务构造说明书(MD)”，实现全场景覆盖。

## 2. 快速使用

### 使用 Claude Code skill
```bash
/mq-sender 批量入仓-新增任务，taskid=387 发送审批通过
/mq-sender 批量入仓-新增任务，taskid=386 发送审批拒绝
/mq-sender 批量入仓-新增任务，taskid=387 模拟审批通过消息发送
/mq-sender 批量入仓-新增任务，taskid=387 模拟审批拒绝消息发送
```

AI 会自动：
1. 识别业务场景（批量入仓-新增任务）
2. 读取对应的协议 MD（`references/JDBC批量入仓_新增任务审批_消息构造协议.md`）
3. 查询数据库获取必需信息
4. 使用协议中的默认值
5. 构造消息并发送
6. 返回执行结果

## 3. 目录说明
- `scripts/mq_sender.py`: 通用发送脚本，内置自动双重序列化功能
- `SKILL.md`: AI 执行指令，定义了 AI 如何工作
- `references/`: 各业务场景的消息构造协议 MD
- `skill.json`: Claude Code skill 配置文件

## 4. 如何增加新业务？
如果你需要模拟一个新的 MQ 消息（例如：XXX 业务回调），你不需要写代码，只需在 `references/` 目录下创建一份新的协议 MD：

### [业务名]_消息构造协议.md（模板）
```markdown
### XXX 业务 MQ 消息构造协议

- **传输层**:
    - **Queue**: `xxx.queue.name`
    - **Cluster**: `amqp-cn-xxxxxx`

- **消息体 (Payload) 结构**:
    - **外层字段清单**:
        1. `field1`: 字段说明
        2. `field2`: 字段说明

    - **内层 `dataMap` 字段清单**:
        1. `subField1`: 字段说明
        2. `subField2`: 字段说明

- **取值逻辑**:
    - **`field1`**: 取自数据库表 `xxx` 的 `yyy` 字段
    - **`field2`**: 默认值 `zzz`

- **数据库查询连接信息以及 SQL**:
```sql
SELECT ... FROM ... WHERE ...
```

- **Host**: `xxx.db.xxx.net`
- **Database**: `xxx`
- **User**: `xxx`
- **Password**: `xxx`
```

创建完 MD 后，用户就可以直接使用自然语言调用了。

## 5. 优势
- **零代码扩展**：添加新业务只需创建 MD 协议文件，无需修改代码
- **免转义**：无需手动拼接 `\”dataMap\”: \”{\\\”id\\\”:123}\”` 这种复杂的转义字符串
- **参数自动化**：AI 自动查询数据库、使用默认值、构造消息
- **自然语言交互**：用户只需用自然语言描述需求即可

## 6. 已支持的业务场景
- ✅ JDBC 批量入仓审批消息（新增任务/新增���段/修改任务/下线任务）

---

## 7. 业务参考文档

### 消息构造协议（Skill 内置）
- [JDBC批量入仓_新增任务审批_消息构造协议](references/JDBC批量入仓_新增任务审批_消息构造协议.md) - 📖 **MQ 消息字段清单、取值逻辑**

### 相关业务流程文档
- [TKI_001: 批量入仓 BPM 审批消息构造指引](../../JBDC入仓/BIZ_REQ_33706_001_批量入仓_新增任务/components/TKI_001_批量入仓 BPM 审批消息构造指引.md) - BPM 审批流程说明
- [TKD_010: BPM记录表](../../JBDC入仓/BIZ_REQ_33706_001_批量入仓_新增任务/components/TKD_010_BPM记录表(dataops_bpm_record).md) - BPM 数据表结构

> 💡 **说明**：消息构造协议在 skill 的 `references/` 目录下，方便 skill 独立使用；业务流程文档统一管理在 `JBDC入仓/` 目录下。