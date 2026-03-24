---
name: test-create-jdbctable
displayName: JDBC 测试表生成器
description: 快生成符合规范的测试表和测试数据，支持 MySQL、TiDB、ADB 等数据库，支持复杂字段类型、索引和唯一键要求等额外需求。
---

# JDBC 测试表生成器

当用户需要快速生成符合规范的测试表和测试数据时，使用此 skill。支持 MySQL、TiDB、ADB 等数据库，可以通过自然语言对话方式使用。

## 适用场景

当用户请求以下内容时，自动触发此 skill:
- 创建测试表
- 生成测试数据
- 生成建表 SQL
- 创建 JDBC 测试表
- 在数据库中创建测试表
- 需要测试表和测试数据
- 生成违反规范的测试表（异常场景测试）
- 生成不符合注释规范的测试表

关键词: 测试表、测试数据、建表、生成表、JDBC、MySQL、TiDB、ADB、数据库测试、造表、异常场景、违反规范、不符合规范、反面测试

## 执行步骤

**重要约束**：
- 当用户使用自然语言描述造表需求后，不要深度思考，直接快速实现
- 只向用户展示关键节点信息（如：正在生成表、执行成功/失败、表名、数据行数等）
- 不要展示详细的执行过程，包括：
  - 完整的 DDL 语句
  - Python 脚本的详细输出
  - 中间步骤的详细日志
- 执行完成后，简洁地告知用户结果即可

### 0. 参数获取方式

**直接命令参数模式（推荐）**：
- 当用户使用 `/test-create-jdbctable [自然语言描述]` 格式调用时，直接解析 [自然语言描述] 部分
- 示例：`/test-create-jdbctable 帮我在dataops-shitingjie这个库创建一个测试用的表`
- 示例：`/test-create-jdbctable 在tidb造一个包含decimal字段的表，插入5条数据`
- 从这个描述中提取所有可能的参数（表名、环境、数据行数、数据类型等）
- 只有在关键参数（如表名）缺失时才使用 AskUserQuestion 询问
- 如果环境信息明确（如"dataops-shitingjie"、"tidb"），直接执行到数据库

**交互式问答模式**：
- 如果用户只输入 `/test-create-jdbctable` 没有提供任何描述，进入交互式问答模式
- 逐步询问必需参数

### 1. 理解用户需求

分析用户的自然语言输入，提取关键信息：

**表名识别**：
- 关键词："表名"、"创建"、"生成"、"叫"、"命名为"
- 示例："创建 test_users 表" → 表名为 test_users
- 示例："帮我造一个订单表" → 建议表名 test_orders

**数据行数识别**：
- 关键词："条"、"行"、"个"、"数据"
- 示例："生成 50 条数据" → 行数为 50
- 示例："插入 100 行" → 行数为 100
- 默认值：如果用户没有指定，使用 10 条

**数据类型识别**：
- 关键词："字符串"、"数字"、"日期"、"布尔"、"混合"、"decimal"
- 示例："包含日期字段" → 数��类型为 date
- 示例："需要 decimal 类型" → 数据类型为 number 或 mixed
- 默认值：如果用户没有指定，使用 mixed（混合类型，推荐）

**环境识别**：
- 直接匹配环境名称：tidb、mysql、cjjcommon、tidb-ares 等
- 示例："在 tidb 环境" → 环境为 tidb-ares
- 示例："在 cjjcommon 库" → 环境为 cjjcommon

**执行意图识别**：
- 关键词："执行"、"创建到"、"写入"、"直接创建"、"造表"
- 示例："执行到数据库" → execute = true
- 示例："只生成 SQL" → execute = false
- 默认值：如果用户说"创建"、"造"，默认为 execute = true

**异常场景识别**：
- 关键词："违反"、"不符合"、"异常"、"反面"、"错误"、"无效"、"不包含中文"、"少于4个字符"
- 示例："生成表注释不包含中文的测试表" → invalidScenario = table_no_chinese
- 示例："创建字段注释少于4���字符的异常测试表" → invalidScenario = field_short
- 示例："生成违反注释规范的测试表" → 询问具体违规场景
- 可用场景：
  - table_no_chinese：表注释不包含中文
  - table_short：表注释少于4个字符
  - field_no_chinese：字段注释不包含中文
  - field_short：字段注释少于4个字符

### 2. 获取必需参数

#### 2.1 表名 (tableName)

**必需参数**，测试表的名称。

**获取方式**：
- 如果用户已经提供了表名，直接使用
- 如果用户没有提供，使用 AskUserQuestion 工具询问表名
- 如果用户只提供了表的用途（如"用户表"），建议表名（如 test_users）

**表名规范**：
- 只能包含小写字母、数字、下划线
- 不能以数字开头
- 建议以 test_ 开头，便于识别测试表

**询问示例**：
```
使用 AskUserQuestion 工具询问：
问题："请问表名是什么？"
选项：
  - test_demo（演示测试表）
  - test_users（用户测试表）
  - test_orders（订单测试表）
  - 自定义表名
```

#### 2.2 数据行数 (rowCount)

**可选参数**，默认值为 10。

**获取方式**：
- 从用户输入中提取数字
- 如果用户没有指定，使用默认值 10
- 建议范围：1-1000 行

### 3. 获取可选参数

#### 3.1 目标环境 (env)

**可选参数**，使用预配置的测试环境。

**可用环境**：
- `cjjcommon` - cjjcommon MySQL 数据库（dataops_shitingjie 库）
- `bigdata-biz-dataops` - bigdata-biz MySQL 数据库（dataops 库）
- `bigdata-biz-datagovernor` - bigdata-biz MySQL 数据库（datagovernor 库）
- `cjjloan` - cjjloan MySQL 数据库（datahub 库）
- `tidb-ares` - TiDB 公共测试环境（ares 库）
- `adb-realtime` - ADB 实时数仓测试环境（stjtestadb 库）

**获取方式**：
- 从用户输入中识别环境名称
- 如果用户说"执行到数据库"但没有指定环境，使用 AskUserQuestion 询问
- 如果用户只说"生成 SQL"，不需要指定环境

**询问示例**：
```
使用 AskUserQuestion 工具询问：
问题："请选择目标环境"
选项：
  - cjjcommon（MySQL - dataops_shitingjie 库）
  - tidb-ares（TiDB - ares 库）（推荐）
  - bigdata-biz-dataops（MySQL - dataops 库）
  - 其他环境
```

#### 3.2 数据类型 (dataType)

**可选参数**，默认值为 mixed。

**可选值**：
- `string` - 字符串类型（VARCHAR、TEXT 等字段）
- `number` - 数值类型（INT、BIGINT、DECIMAL、FLOAT 等字段）
- `date` - 日期时间类型（DATE、DATETIME、TIMESTAMP 等字段）
- `boolean` - 布尔类型（TINYINT 字段）
- `mixed` - 混合类型（包含多种类型字段，推荐）

**获取方式**：
- 从用户描述中识别关键词
- 如果用户没有明确指定，使用默认值 mixed

#### 3.3 其他参数

- `tableComment` - 表注释（可选，默认自动生成）
- `includeDrop` - 是否包含 DROP TABLE 语句（可选，默认 false）
- `output` - 输出文件路径（可选，如果用户要保存到文件）

### 4. 调用测试表生成器

根据收集到的参数，使用 Bash 工具调用测试表生成器脚本。

**脚本路径**：
```
test-table/scripts/index.py
```

**调用方式**：

**方式 1：列出所有预配置环境**
```bash
cd test-table/scripts && python index.py list-envs
```

**方式 2：生成 SQL（不执行到数据库）**
```bash
cd test-table/scripts && python index.py generate \
  --tableName {表名} \
  --dataType {数据类型} \
  --rowCount {行数}
```

**方式 3：生成并执行到数据库**
```bash
cd test-table/scripts && python index.py generate \
  --tableName {表名} \
  --dataType {数据类型} \
  --rowCount {行数} \
  --execute \
  --env {环境名称}
```

**方式 4：生成异常场景测试表（违反注释规范）**
```bash
cd test-table/scripts && python index.py generate \
  --tableName {表名} \
  --rowCount {行数} \
  --invalidScenario {异常场景类型} \
  --execute \
  --env {环境名称}
```

异常场景类型：
- `table_no_chinese` - 表注释不包含中文
- `table_short` - 表注释少于4个字符
- `field_no_chinese` - 字段注释不包含中文
- `field_short` - 字段注释少于4个字符

**参数说明**：
- `--tableName` - 表名（必需）
- `--dataType` - 数据类型（可选，默认 mixed）
- `--rowCount` - 数据行数（可选，默认 10）
- `--dbType` - 数据库类型（可选，默认 mysql）
- `--tableComment` - 表注释（可选）
- `--execute` - 执行到数据库（可选标志）
- `--env` - 环境名称（可选）
- `--output` - 输出文件路径（可选）
- `--includeDrop` - 包含 DROP TABLE（可选标志）

### 5. 解析和展示结果

根据执行结果，以清晰的格式展示给用户。

#### 5.1 列出环境（list-envs）

**展示格式**：
```
预配置的测试环境：

1. cjjcommon (MySQL)
   - 主机: cjjcommon.db.ali-bj-sit01.shuheo.net
   - 数据库: dataops_shitingjie
   - 说明: cjjcommon 数据库 - dataops_shitingjie 库

2. tidb-ares (TiDB)
   - 主机: sitpublic.tidb.ali-bj-sit01.shuheo.net
   - 数据库: ares
   - 说明: TiDB 公共测试环境 - ares 库

[显示所有环境]
```

#### 5.2 仅生成 SQL（不执行）

**展示格式**：
```
✅ 测试表 SQL 生成成功

表信息:
- 表名: {表名}
- 数据类型: {数据类型}
- 数据行数: {行数}
- 数据库类型: {数据库类型}

生成的 SQL 脚本:
----------------------------------------
[显示建表语句和插入语句]
----------------------------------------

提示:
- 如需执行到数据库，请告诉我目标环境
- 如需保存到文件，请告诉我文件路径
```

#### 5.3 执行到数据库（成功）

**展示格式**：
```
✅ 测试表创建成功

执行信息:
- 表名: {表名}
- 目标环境: {环境名称}
- 数据库: {数据库名}
- 主机: {主机地址}
- 执行语句数: {语句数} 条

下一步:
- 可以使用 SQL 客户端连接数据库查看数据
- 表结构符合 MySQL 建表规范
- 所有字段都有注释和索引
```

#### 5.4 执行到数据库（失败）

**展示格式**：
```
❌ 测试表创建失败

失败原因: {错误信息}

请检查:
1. 数据库连接是否正常
2. 账号是否有 CREATE TABLE 权限
3. 表名是否已存在（如需覆盖，请使用 --includeDrop 参数）
4. 网络连接是否正常

建议:
- 可以先生成 SQL 查看内容
- 检查配置文件中的密码是否正确
- 尝试使用其他环境
```

## 数据结构

### 数据类型模板

#### string - 字符串类型

包含字段：
- `id` (BIGINT UNSIGNED) - 主键，自增
- `user_name` (VARCHAR(100)) - 用户姓名
- `email` (VARCHAR(255)) - 电子邮箱
- `description` (TEXT) - 详细描述
- `created_at` (TIMESTAMP) - 创建时间
- `updated_at` (TIMESTAMP) - 更新时间
- 索引：`idx_updated_at` (updated_at)

#### number - 数值类型

包含字段：
- `id` (BIGINT UNSIGNED) - 主键，自增
- `int_value` (INT) - 整数值
- `bigint_value` (BIGINT) - 长整数值
- `decimal_value` (DECIMAL(10,2)) - 小数值
- `price` (DECIMAL(7,5)) - 价格
- `amount` (DECIMAL(15,4)) - 金额
- `rate` (DECIMAL(5,2)) - 比率
- `float_value` (FLOAT) - 浮点数值
- `created_at` (TIMESTAMP) - 创建时间
- `updated_at` (TIMESTAMP) - 更新时间
- 索引：`idx_updated_at` (updated_at)

#### date - 日期时间类型

包含字段：
- `id` (BIGINT UNSIGNED) - 主键，自增
- `date_value` (DATE) - 日期值
- `datetime_value` (DATETIME) - 日期时间值
- `timestamp_value` (TIMESTAMP) - 时间戳值
- `year_value` (YEAR) - 年份值
- `created_at` (TIMESTAMP) - 创建时间
- `updated_at` (TIMESTAMP) - 更新时间
- 索引：`idx_updated_at` (updated_at)

#### boolean - 布尔类型

包含字段：
- `id` (BIGINT UNSIGNED) - 主键，自增
- `is_active` (TINYINT) - 是否激活
- `is_deleted` (TINYINT) - 是否删除
- `is_verified` (TINYINT) - 是否验证
- `created_at` (TIMESTAMP) - 创建时间
- `updated_at` (TIMESTAMP) - 更新时间
- 索引：`idx_updated_at` (updated_at)

#### mixed - 混合类型（推荐）

包含字段：
- `id` (BIGINT UNSIGNED) - 主键，自增
- `user_name` (VARCHAR(100)) - 用户姓名
- `age` (INT) - 年龄
- `salary` (DECIMAL(10,2)) - 薪资
- `birth_date` (DATE) - 出生日期
- `is_active` (TINYINT) - 是否激活
- `description` (TEXT) - 详细描述
- `created_at` (TIMESTAMP) - 创建时间
- `updated_at` (TIMESTAMP) - 更新时间
- 索引：`idx_updated_at` (updated_at)

### 建表规范

所有生成的表都符合以下规范（基于 references/JDBC_sql_verify_rules.md）：

**表级规范**：
- 表名使用小写字母、数字、下划线，不能以数字开头
- 表必须有主键
- 表必须有表注释
- 表字符集使用 utf8mb4
- 表引擎使用 InnoDB

**字段级规范**：
- 主键名称为 `id`
- 主键类型为 `BIGINT UNSIGNED`
- 主键必须自增（AUTO_INCREMENT）
- 字段名使用小写字母、数字、下划线
- 字段必须有注释
- 包含 `created_at` 和 `updated_at` 时间字段
- `updated_at` 字段有索引

**时间字段规范**：
- `created_at` 默认值为 CURRENT_TIMESTAMP
- `updated_at` 默认值为 CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP

## 使用场景

### 场景 1: 自然语言快速生成测试表

用户用自然语言描述需求，系统自动解析并生成测试表。

**交互示例**：
```
用户: 帮我创建一个用户表，包含 50 条测试数据

助手: 好的，我来帮你创建用户测试表。

我理解你的需求：
- 数据行数：50
- 数据类型：mixed（混合类型，推荐）

请问表名是什么？

用户: test_users

助手: 收到。是否需要直接执行到数据库？

用户: 是的，执行到 tidb 环境

助手: [调用脚本执行]

✅ 测试表创建成功

执行信息:
- 表名: test_users
- 目标环境: tidb-ares
- 数据库: ares
- 主机: sitpublic.tidb.ali-bj-sit01.shuheo.net
- 执行语句数: 51 条（1 条建表 + 50 条插入）
```

### 场景 2: 快速造表（简化版）

用户提供最少信息，系统自动补充默认值。

**交互示例**：
```
用户: 帮我在 tidb 造一个普通测试表

助手: 好的，我来在 TiDB 环境创建测试表。

[自动使用默认值：表名 test_tidb_sample，数据类型 mixed，行数 10]

✅ 测试表创建成功
- 表名: test_tidb_sample
- 数据: 10 条
```

### 场景 3: 生成包含特定字段类型的表

用户需要特定类型的字段（如 decimal）。

**交互示例**：
```
用户: 帮我在 cjjcommon 库创建一个表，需要包含 decimal 字段，插入 2 条数据

助手: 好的，我来创建包含 decimal 字段的测试表。

[识别需求：decimal 字段 → 使用 mixed 或 number 类型]

请问表名是什么？

用户: 表名以 cc_test 开头

助手: [建议表名 cc_test_decimal_demo]

✅ 测试表创建成功
- 表名: cc_test_decimal_demo
- 包含字段: salary (DECIMAL(10,2))
- 数据: 2 条
```

### 场景 4: 仅生成 SQL 不执行

用户需要查看 SQL 内容或手动执行。

**交互示例**：
```
用户: 生成一个订单表的 SQL，不要执行

助手: 好的，我来生成订单表的 SQL 脚本。

[生成 SQL 并显示]

提示:
- 如需执行到数据库，请告诉我目标环境
- 如需保存到文件，请告诉我文件路径
```

### 场景 5: 生成异常场景测试表（违反注释规范）

用户需要测试异常场景，生成违反 MySQL 注释规范的测试表。

**交互示例**：
```
用户: 帮我生成一个表注释不包含中文的测试表，用于异常场景测试

助手: 好的，我来生成违反注释规范的测试表。

[识别异常场景：table_no_chinese]

请问表名是什么？

用户: test_invalid_comment

助手: 是否需要执行到数据库？

用户: 是的，执行到 cjjcommon 环境

助手: [调用脚本执行]

✅ 异常场景测试表创建成功
- 表名: test_invalid_comment
- 异常场景: 表注释不包含中文
- 数据: 2 条
```


## 注意事项

### 1. 自然语言解析

系统会自动从用户的自然语言输入中提取关键信息：

**表名识别**：识别关键词"表名"、"创建"、"生成"等，如果用户只提供用途会建议表名

**数据行数识别**：识别关键词"条"、"行"、"个"等，默认值为 10

**环境识别**：识别环境名称如 tidb、mysql、cjjcommon 等

**执行意图识别**：如果用户说"创建"、"造表"默认会执行到数据库

### 2. 参数验证

**表名规范**：只能包含小写字母、数字、下划线，不能以数字开头，建议以 test_ 开头

**数据行数限制**：建议范围 1-1000 行

**数据库权限**：确保账号有 CREATE TABLE 和 INSERT 权限

### 3. 表名冲突处理

如果表已存在会报错，可以使用 `--includeDrop` 参数先删除旧表

### 4. 密码安全

配置文件中的密码为明文存储，仅用于测试环境

### 5. 配置文件更新

配置文件路径：`scripts/db_config.ini`，参考文档：`references/JDBC_sit_connnect_info.md`
