---
name: metadata-complete
displayName: 元数据完整性管理
description: 自动化执行 MySQL（TIDB/ADB） 库表元数据完整性管理，串联调用 GET 和 POST 接口完成元数据查询、字段补充和管理操作
---

# 元数据完整性管理 Skill

当用户需要管理 MySQL 库表元数据、补充字段属性或进行元数据完整性检查时，使用此 skill。自动串联 GET 和 POST 接口完成完整的管理流程。

## 适用场景

当用户请求以下内容时，自动触发此 skill：
- 管理表的元数据
- 补充字段属性
- 完善表的元数据信息
- 元数据完整性检查
- 批量补充字段属性
- 为表添加固定字段标识

关键词：元数据、metadata、字段属性、完整性、补充字段、元数据管理、表属性

## 执行步骤

**重要约束**：
- 当用户使用自然语言描述元数据管理需求后，快速理解意图并执行
- 只向用户展示关键节点信息（如：正在查询、正在处理、成功/失败、影响字段数等）
- 不要展示详细的 API 请求响应内容
- 执行完成后，简洁地告知用户结果即可

### 0. 参数获取方式

**直接命令参数模式（推荐）**：
- 当用户使用 `/metadata-complete [自然语言描述]` 格式调用时，直接解析 [自然语言描述] 部分
- 示例：`/metadata-complete 帮我管理 dataops_shitingjie.user_info 表的元数据`
- 示例：`/metadata-complete 补充 cjjcommon 实例下 test_table 的字段属性`
- 从这个描述中提取所有可能的参数（实例、数据库、表名）
- 只有在关键参数（如表名）缺失时才使用 AskUserQuestion 询问

**交互式问答模式**：
- 如果用户只输入 `/metadata-complete` 没有提供任何描述，进入交互式问答模式
- 逐步询问必需参数

### 1. 理解用户需求

分析用户的自然语言输入，提取关键信息：

**实例识别**：
- 关键词："实例"、"instance"、"cjjcommon"、"bigdata-biz"、"cjjloan" 等
- 示例："cjjcommon 实例" → instance = "cjjcommon"
- 示例："在 bigdata-biz 数据库" → instance = "bigdata-biz"

**数据库识别**：
- 关键词："数据库"、"database"、"库"
- 格式识别："数据库.表名" 或 "库名.表名"
- 示例："dataops_shitingjie.user_info" → database = "dataops_shitingjie", table = "user_info"
- 示例："在 dataops 库的 test_table" → database = "dataops", table = "test_table"

**表名识别**：
- 关键词："表"、"table"、"表名"
- 格式识别：单独的表名或 "库.表" 格式
- 示例："user_info 表" → table = "user_info"
- 示例："test_table" → table = "test_table"

**操作权限识别**：
- 更新权限关键词："支持更新"、"可更新"、"允许更新"、"existUpdate"
- 删除权限关键词："支持删除"、"可删除"、"允许删除"、"临时表"、"existDelete"
- 默认值：existUpdate = true, existDelete = false

### 2. 获取必需参数

#### 2.1 实例名称 (instance)

**必需参数**，MySQL 实例标识。

**常用实例**：
- `cjjcommon` - cjjcommon MySQL 数据库
- `bigdata-biz` - bigdata-biz MySQL 数据库
- `cjjloan` - cjjloan MySQL 数据库

**获取方式**：
- 如果用户已经提供了实例名，直接使用
- 如果用户没有提供，使用 AskUserQuestion 工具询问

**询问示例**：
```
使用 AskUserQuestion 工具询问：
问题："请选择 MySQL 实例"
选项：
  - cjjcommon（常用测试实例）（推荐）
  - bigdata-biz（bigdata-biz 实例）
  - cjjloan（cjjloan 实例）
  - 自定义实例名
```

#### 2.2 数据库名称 (database)

**必需参数**，数据库名称。

**常用数据库**（根据实例）：
- cjjcommon 实例：`dataops_shitingjie`
- bigdata-biz 实例：`dataops`, `datagovernor`
- cjjloan 实例：`datahub`

**获取方式**：
- 如果用户提供了 "库.表" 格式，从中提取数据库名
- 如果用户单独提供了数据库名，直接使用
- 如果用户没有提供，使用 AskUserQuestion 工具询问

**询问示例**：
```
使用 AskUserQuestion 工具询问：
问题："请输入数据库名称"
选项：
  - dataops_shitingjie（cjjcommon 实例常用库）（推荐）
  - dataops（bigdata-biz 实例常用库）
  - datagovernor（bigdata-biz 实例常用库）
  - 自定义数据库名
```

#### 2.3 表名 (table)

**必需参数**，数据表名称。

**获取方式**：
- 如果用户提供了 "库.表" 格式，从中提取表名
- 如果用户单独提供了表名，直接使用
- 如果用户没有提供，使用 AskUserQuestion 工具询问

**询问示例**：
```
使用 AskUserQuestion 工具询问：
问题："请输入表名"
提示：输入要管理元数据的表名称
```

### 3. 获取可选参数

#### 3.1 更新权限 (existUpdate)

**可选参数**，默认值为 true。

表示表数据是否支持更新操作。

**获取方式**：
- 从用户输入中识别关键词
- 默认值为 true（大多数业务表支持更新）

#### 3.2 删除权限 (existDelete)

**可选参数**，默认值为 false。

表示表数据是否支持删除操作。

**获取方式**：
- 从用户输入中识别关键词
- 如果用户提到"临时表"、"测试表"，建议设为 true
- 默认值为 false（大多数业务表不支持删除）

### 4. 调用元数据管理工具

根据收集到的参数，使用 Bash 工具调用元数据管理脚本。

**脚本路径**：
```
metadata-complete/scripts/index.py
```

**调用方式**：

```bash
cd metadata-complete/scripts && python index.py \
  --instance {实例名} \
  --database {数据库名} \
  --table {表名} \
  --existUpdate {true|false} \
  --existDelete {true|false}
```

**参数说明**：
- `--instance` - MySQL 实例标识（必需）
- `--database` - 数据库名称（必需）
- `--table` - 数据表名称（必需）
- `--existUpdate` - 是否支持更新（可选，默认 true）
- `--existDelete` - 是否支持删除（可选，默认 false）

**示例命令**：

**普通业务表**：
```bash
cd metadata-complete/scripts && python index.py \
  --instance cjjcommon \
  --database dataops_shitingjie \
  --table user_info
```

**临时测试表（支持删除）**：
```bash
cd metadata-complete/scripts && python index.py \
  --instance cjjcommon \
  --database dataops_shitingjie \
  --table temp_table \
  --existDelete true
```

**只读历史表（不支持更新）**：
```bash
cd metadata-complete/scripts && python index.py \
  --instance cjjcommon \
  --database dataops_shitingjie \
  --table history_table \
  --existUpdate false
```

### 5. 解析和展示结果

根据执行结果，以清晰的格式展示给用户。

#### 5.1 执行成功

**展示格式**：
```
✅ 元数据管理完成

表信息：
- 实例：{实例名}
- 数据库：{数据库名}
- 表名：{表名}
- 更新权限：{是否支持}
- 删除权限：{是否支持}

处理结果：
- 已为 {N} 个字段补充固定属性
- 元数据管理接口调用成功
```

#### 5.2 执行失败

**展示格式**：
```
❌ 元数据管理失败

失败原因：{错误信息}

请检查：
1. 实例、数据库、表名是否正确
2. 表是否存在
3. 网络连接是否正常
4. API 接口是否可访问

建议：
- 确认表名拼写正确
- 检查网络连接到 SIT03 环境
- 查看详细日志了解失败原因
```

## 功能说明

### 核心功能

这个 skill 用于自动化执行 MySQL 库表元数据的完整性管理流程，实现以下功能：

1. **查询元数据**：调用 GET 接口获取库表的完整元数据信息
2. **数据处理**：自动补充必需的 5 个固定字段（canNotBeModified, columnEditing, sensitive, json, enumerated）
3. **管理元数据**：调用 POST 接口完成元数据管理操作

### 接口串联逻辑

```
步骤1: GET /firekylin/mysql-metadata/mysql/table/metadata
         ↓
步骤2: 解析响应 + 补充 columnMetadata 字段
         ↓
步骤3: POST /firekylin/mysql-metadata/mysql/table/metadata:manage
```

### 补充的固定字段

每个字段都会自动补充以下 5 个属性（默认值均为 false）：

1. **canNotBeModified** - 字段是否不可修改
2. **columnEditing** - 字段是否可编辑
3. **sensitive** - 字段是否敏感
4. **json** - 字段是否为 JSON 类型
5. **enumerated** - 字段是否为枚举类型

## 使用场景

### 场景 1：自然语言管理元数据

用户用自然语言描述需求，系统自动解析并执行元数据管理。

**交互示例**：
```
用户：帮我管理 dataops_shitingjie.user_info 表的元数据

助手：好的，我来为你管理 user_info 表的元数据。

我理解你的需求：
- 实例：cjjcommon
- 数据库：dataops_shitingjie
- 表：user_info

[调用脚本执行]

✅ 元数据管理完成
- 已为 12 个字段补充固定属性
- 元数据管理接口调用成功
```

### 场景 2：使用库.表格式

用户提供简洁的库.表格式。

**交互示例**：
```
用户：/metadata-complete 补充 cjjcommon 的 dataops.test_table 元数据

助手：好的，我来补充 test_table 的元数据。

[自动解析：instance=cjjcommon, database=dataops, table=test_table]

✅ 元数据管理完成
- 已为 8 个字段补充固定属性
```

### 场景 3：指定权限设置

用户需要特定的权限配置。

**交互示例**：
```
用户：帮我管理 temp_table 的元数据，这是一个临时表，需要支持删除

助手：好的，我来管理临时表的元数据。

[识别关键词"临时表" → existDelete=true]

请确认参数：
- 更新权限：支持
- 删除权限：支持（临时表）

✅ 元数据管理完成
- 表配置为可删除
```

### 场景 4：批量处理多个表

用户需要处理多个表的元数据。

**交互示例**：
```
用户：帮我批量管理这几个表的元数据：
- user_info
- order_info
- product_info

助手：好的，我来为这 3 个表管理元数据。

请问这些表在哪个数据库？

用户：都在 cjjcommon 的 dataops_shitingjie 库

助手：[依次调用脚本处理每个表]

✅ 批量处理完成
- user_info: 12 个字段 ✓
- order_info: 15 个字段 ✓
- product_info: 10 个字段 ✓
```

## 注意事项

### 1. 参数格式

**支持的格式**：
- "库.表" 格式：`dataops_shitingjie.user_info`
- 分开描述：`dataops_shitingjie 库的 user_info 表`
- 实例+库+表：`cjjcommon 实例的 dataops.test_table`

### 2. 实例映射

常用实例及其对应的数据库：

| 实例 | 常用数据库 | 说明 |
|------|-----------|------|
| cjjcommon | dataops_shitingjie | 常用测试库 |
| bigdata-biz | dataops, datagovernor | 大数据业务库 |
| cjjloan | datahub | 贷款业务库 |

### 3. 权限设置建议

**更新权限（existUpdate）**：
- 业务表：建议 true（默认）
- 历史表：建议 false
- 日志表：建议 false

**删除权限（existDelete）**：
- 业务表：建议 false（默认）
- 临时��：建议 true
- 测试表：建议 true

### 4. 人员信息

脚本中已固定人员信息：
- p_n（人员名称）：施婷杰
- p_u（人员ID）：71e8b23d-45e2-497a-b247-f5b807fb4f65

无需用户提供，自动使用固定值。

### 5. 网络环境

需要能够访问 SIT03 环境：
- 基础 URL：http://firekylin.apps01.ali-bj-sit03.shuheo.net
- GET 接口：/firekylin/mysql-metadata/mysql/table/metadata
- POST 接口：/firekylin/mysql-metadata/mysql/table/metadata:manage

### 6. 执行流程

完整的执行流程包括：
1. 查询元数据（GET 请求）
2. 解析响应数据
3. 补充 5 个固定字段
4. 提交管理请求（POST 请求）
5. 返回执行结果

任何步骤失败都会终止流程并报告错误。

## 参考文档

- **[README.md](README.md)** - 快速入门指南
- **[SKILL_USAGE.md](SKILL_USAGE.md)** - 详细使用说明
- **[API_information.md](references/API_information.md)** - API 接口文档
- **[USAGE_EXAMPLES.md](scripts/USAGE_EXAMPLES.md)** - 脚本使用示例

## 测试数据

可以使用以下测试表验证功能：
- 实例：cjjcommon
- 数据库：dataops_shitingjie
- 表：0418bugfuxianccc

测试命令：
```bash
/metadata-complete 管理 cjjcommon 的 dataops_shitingjie.0418bugfuxianccc
```
