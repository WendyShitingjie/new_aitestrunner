---
name: jdbc-warehouse-test
displayName: JDBC入仓批量测试文件生成器
description: 生成符合 JDBC 批量入仓接口规范的 xlsx 测试文件，支持成功场景和多种异常场景
---

# JDBC 入仓批量测试文件生成器

当用户需要生成 JDBC 入仓批量操作的测试文件时，使用此 skill。自动生成符合 `/dataops/etlx/batch/v2/validate` 接口规范的 23 列 xlsx 测试文件。

## 适用场景

当用户请求以下内容时，自动触发此 skill:
- 生成 JDBC 入仓测试文件
- 生成批量入仓测试数据
- 生成 validate 接口测试文件
- 创建批量操作测试 xlsx
- 生成异常场景测试文件
- **批量生成多个表的测试文件**（新功能）
- **一键式完整工作流：造表→完善元数据→生成测试文件**（新功能）

关键词: JDBC入仓、批量测试、测试文件、xlsx、validate接口、批量操作、异常场景、批量入仓、多个表、N个表

## 执行步骤

**重要约束**：
- 当用户使用自然语言描述需求后，快速理解意图并执行
- 只向用户展示关键节点信息（正在生成、成功/失败、文件路径等）
- 不要展示详细的字段内容和生成过程
- 执行完成后，简洁地告知用户结果和文件位置

### 0. 智能默认参数策略

当用户请求生成测试文件但未提供完整参数时，使用以下默认值：

| 数据源类型 | 默认实例 | 默认数据库 | 默认抽数方式 | 默认处理方式 |
|-----------|---------|-----------|-------------|-------------|
| **mysql** | cjjcommon | dataops_shitingjie | ins | merge |
| **tidb** | sitpublic | ares | all | all |
| **adb** | sitadbrealtimedw | stjtestadb | ins | merge |

**应用规则**：
- 表名是唯一必需参数，必须由用户提供或询问
- 如果用户明确指定了实例/数据库，优先使用用户指定的值
- 示例：用户说"帮我造一个 mysql 入仓的测试 excel，表名是 test_table_01"
  → 自动使用：cjjcommon.dataops_shitingjie.test_table_01，不需要询问其他参数

### 1. 参数获取方式

**直接命令参数模式（推荐）**：
- 当用户使用 `/jdbc-warehouse-test [自然语言描述]` 格式调用时，直接解析描述部分
- 示例：`/jdbc-warehouse-test 为 stjtestadb.adb_json_batch_01 生成测试文件`
- 示例：`/jdbc-warehouse-test 克隆 adb_json_batch_01 并生成成功场景测试文件`
- 示例：`/jdbc-warehouse-test 为 test_table 生成字段缺失异常场景`
- **批量模式示例**：`/jdbc-warehouse-test 生成包含 3 个表的批量测试文件`
- **一键式示例**：`/jdbc-warehouse-test 在 cjjcommon 生成 2 个表的批量入仓测试文件`

### 2. 理解用户需求

分析用户的自然语言输入，提取关键信息：

**功能类型识别**（按优先级）：

1. **批量工作流**（最优先，推荐）：关键词"批量"、"多个表"、"N个表"、"包含X个"
   - 示例："生成包含 3 个表的批量测试文件"
   - 示例："在 cjjcommon 生成 2 个表的批量入仓测试"
   - **这是真正的批量入仓**：一份 Excel 包含多行数据，每行对应一个表
   - 调用 `batch_workflow.py` 脚本

2. **模板更新**（已有表场景）：关键词"更新"、"已有表"、"现有表"、指定多个表名
   - 示例："为 test_table_01, test_table_02, test_table_03 生成测试文件"
   - 示例："更新 3 个表的测试文件"
   - 表已存在且元数据已完善
   - 调用 `template_updater.py` 脚本

3. **基于已有表**：关键词"为"、"生成"、"基于"
   - 示例："为 stjtestadb.table_name 生成测试文件"
   - 调用 `index.py generate` 命令

4. **先造表再生成**：关键词"克隆"、"复制"、"并生成"
   - 示例："克隆 adb_json_batch_01 并生成测试文件"
   - 调用 `index.py generate --createTable` 命令

**表信息识别**：
- 数据库.表名格式：`stjtestadb.table_name`
- 单独表名：需要询问数据库

**场景类型识别**：
- 成功场景：关键词"成功"、"正常"、"发布"、默认
- 异常场景：关键词"失败"、"异常"、"错误"、具体错误类型
  - F001: 字段缺失
  - F002: 字段格式错误
  - F003: 联动规则冲突
  - F004: 元数据未完善

**数据源类型识别**：
- mysql: 关键词"mysql"、"cjjcommon"、"bigdata-biz"
- tidb: 关键词"tidb"、"ares"
- adb: 关键词"adb"、"stjtestadb"、默认根据数据库名推断

**表数量识别**（用于批量工作流）：
- 从自然语言中提取数字："3 个表"、"2 个"、"包含 5 个"
- 默认值：1 个表
- 限制：最多 3 个表（自动限制，超过则警告）

### 3. 调用测试文件生成器

根据收集到的参数和功能类型，选择合适的脚本调用。

#### 方式 1：批量工作流（⭐ 最推荐）

**适用场景**：用户请求批量生成多个表的测试文件

**脚本路径**：
```
jdbc-warehouse-test/scripts/batch_workflow.py
```

**调用命令**：
```bash
cd jdbc-warehouse-test/scripts && \
python batch_workflow.py {实例名} {数据库名} \
  --count {表数量} \
  --prefix {表名前缀} \
  --db-type {数据库类型} \
  --extract-method {抽数方式} \
  --deal-method {处理方式}
```

**参数说明**：
- `实例名` - 实例名称（必需），如：cjjcommon、tidb-ares
- `数据库名` - 数据库名称（必需），如：dataops_shitingjie、ares
- `--count` - 表数量（可选，默认 1，最大 3）
- `--prefix` - 表名前缀（可选，默认 batch_test）
- `--db-type` - 数据库类型（可选，默认 mysql）
- `--extract-method` - 抽数方式（可选，默认 ins）
- `--deal-method` - 处理方式（可选，默认 merge）

**示例**：
```bash
# 生成 3 个表的批量测试文件
python batch_workflow.py cjjcommon dataops_shitingjie --count 3

# TiDB 环境 2 个表
python batch_workflow.py tidb-ares ares --count 2 --db-type tidb
```

**脚本自动执行**：
1. 创建 N 个测试表（自动生成表名，格式：{prefix}_{timestamp}_{序号}）
2. 完善 N 个表的元数据
3. 生成批量上传文件（N 行数据）

#### 方式 2：模板更新器

**适用场景**：表已存在且元数���已完善

**脚本路径**：
```
jdbc-warehouse-test/scripts/template_updater.py
```

**调用命令**：
```bash
cd jdbc-warehouse-test/scripts && \
python template_updater.py {实例名} {数据库名} {表名1} [表名2] [表名3] \
  --db-type {数据库类型} \
  --extract-method {抽数方式} \
  --deal-method {处理方式}
```

**示例**：
```bash
# 单表
python template_updater.py cjjcommon dataops_shitingjie test_table_01

# 多表（最多 3 个）
python template_updater.py cjjcommon dataops_shitingjie \
  test_table_01 test_table_02 test_table_03
```

#### 方式 3：基于已有表生成（传统）
**脚本路径**：
```
jdbc-warehouse-test/scripts/index.py
```

```bash
cd jdbc-warehouse-test/scripts && \
python index.py generate \
  --database {数据库名} \
  --table {表名} \
  --scenario {场景类型}
```

#### 方式 4：先造表再生成（集成模式，传统）
```bash
cd jdbc-warehouse-test/scripts && \
python index.py generate \
  --sourceTable {源表名} \
  --env {环境名} \
  --scenario {场景类型} \
  --createTable
```

**参数说明**：
- `--database` - 数据库名称（必需，或通过 --env 推断��
- `--table` - 表名（必需）
- `--scenario` - 测试场景（可选，默认 success）
  - `success` - 成功场景
  - `failed_F001` - 字段缺失
  - `failed_F002` - 字段格式错误
  - `failed_F003` - 联动规则冲突
  - `failed_F004` - 元数据未完善
- `--sourceTable` - 源表名（仅在 createTable 模式需要）
- `--env` - 环境名（可选，如 adb-realtime）
- `--createTable` - 是否先创建表（可选标志）
- `--dbType` - 数据源类型（可选，默认自动推断）

### 4. 工作流程

```
用户请求
   ↓
解析参数
   ↓
[可选] 调用 test-table skill 创建表
   ↓
[可选] 调用 metadata-complete skill 完善元数据
   ↓
读取表结构和元数据
   ↓
根据场景类型读取构造规则
   ↓
生成 23 列 XLSX 文件
   ↓
保存到: skills/jdbc-warehouse-test/test_excel/
   ↓
返回文件路径
```

**重要规则**：
- ⚠️ **跳过元数据完善条件**：当用户明确说明测试表**已经完善元数据**时，无需调用 metadata-complete skill，直接进入读取表结构阶段
- 示例：用户说"这个表元数据已经完善好了，帮我生成测试文件" → 跳过 metadata-complete
- 目的：避免重复执行元数据完善操作，提高测试效率

### 5. 解析和展示结果

根据执行结果，以清晰的格式展示给用户。

#### 4.1 执行成功

**展示格式**：
```
✅ 测试文件生成成功

文件信息：
- 场景类型：{场景名称}
- 数据库：{数据库名}
- 表名：{表名}
- 文件路径：skills/jdbc-warehouse-test/test_excel/batch_xxx.xlsx

下一步：
- 可以使用此文件调用 /dataops/etlx/batch/v2/validate 接口
- 文件包含 23 列，符合接口规范
```

#### 4.2 执行失败

**展示格式**：
```
❌ 测试文件生成失败

失败原因：{错误信息}

请检查：
1. 表是否存在
2. 元数据是否已完善
3. 数据库连接是否正常

建议：
- 确认表名拼写正确
- 检查是否需要先执行 test-table 和 metadata-complete
```

## 功能说明

### 核心功能

1. **自动读取表结构**：从数据库读取表的完整元数据信息
2. **智能字段映射**：根据表信息自动填充 23 个必需字段
3. **场景化生成**：支持成功场景和多种异常场景
4. **集成工作流**：可选集成 test-table 和 metadata-complete

### 生成的文件包含 23 列

| 列号 | 字段名称 | 说明 |
|------|---------|------|
| 1 | 数据源类型 | mysql/tidb/adb |
| 2 | 实例 | 从表信息自动获取 |
| 3 | 库 | 从表信息自动获取 |
| 4 | 表 | 从表信息自动获取 |
| 5-10 | 人员信息 | 固定值（施婷杰等） |
| 11-23 | 任务配置 | 根据场景和规则生成 |

### 支持的测试场景

**成功场景**：
- 全量覆盖模式（all-all）
- 增量合并模式（ins-merge）
- 增量分区模式（ins-ins）

**异常场景**：
- F001: 字段缺失（缺少必需字段）
- F002: 字段格式错误（格式不符合规范）
- F003: 联动规则冲突（抽数方式和处理方式不匹配）
- F004: 元数据未完善（表存在但未完善元数据）

## 使用示例

### 示例 1：为已有表生成成功场景测试文件

```
用户：为 stjtestadb.adb_json_batch_01_0227 生成测试文件

助手：[自动解析]
- 数据库：stjtestadb
- 表名：adb_json_batch_01_0227
- 场景：success（默认）

✅ 测试文件生成成功
- 文件路径：skills/jdbc-warehouse-test/test_excel/batch_success_adb_json_batch_01_0227_20260227.xlsx
```

### 示例 2：克隆表并生成测试文件

```
用户：克隆 adb_json_batch_01 并生成测试文件

助手：[执行流程]
1. 调用 test-table 克隆表 → adb_json_batch_01_0227
2. 调用 metadata-complete 完善元数据
3. 生成测试文件

✅ 完成
- 新表：adb_json_batch_01_0227
- 测试文件：batch_success_adb_json_batch_01_0227_20260227.xlsx
```

### 示例 3：生成异常场景测试文件

```
用户：为 test_table 生成字段缺失异常场景

助手：[识别场景]
- 场景：failed_F001（字段缺失）

✅ 测试文件生成成功
- 场景：字段缺失异常
- 文件路径：skills/jdbc-warehouse-test/test_excel/batch_failed_F001_test_table_20260227.xlsx
```

## 注意事项

### 1. 前置依赖

生成测试文件前，表必须：
- ✅ 在数据库中物理存在
- ✅ 元数据已完善（通过 metadata-complete）

### 2. 文件输出位置

所有生成的文件统一输出到：
```
JBDC入仓/BIZ_REQ_33706_001_批量入仓_新增任务/test_data/
```

### 3. 字段映射规则

详细的字段映射规则请参考 `scripts/config.py` 中的配置定义。

### 4. 业务文档

各种测试场景的详细构造方法请参考业务文档：
- [TKI_007](../../JBDC入仓/BIZ_REQ_33706_001_批量入仓_新增任务/components/TKI_007_批量入仓_新增任务_构建正确导入文件指引.md)

## 参考文档

- **[README.md](README.md)** - 详细使用说明
- **[scripts/config.py](scripts/config.py)** - 配置和规则定义
- **[TKI_007](../../JBDC入仓/BIZ_REQ_33706_001_批量入仓_新增任务/components/TKI_007_批量入仓_新增任务_构建正确导入文件指引.md)** - 业务接口说明
