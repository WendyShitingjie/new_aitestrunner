# JDBC 入仓批量测试文件生成器

> 自动生成符合 JDBC 批量入仓接口规范的 xlsx 测试文件

## 🎯 功能概述

这个 skill 用于自动化生成 `/dataops/etlx/batch/v2/validate` 接口所需的测试文件。支持：

- ✅ 自动读取表结构和元数据
- ✅ 智能生成 23 列标准字段
- ✅ 支持多种测试场景（成功/失败）
- ✅ 集成 test-table 和 metadata-complete
- ✅ 规范化文件命名和存储
- ✨ **模板更新器**：避免文件爆炸，快速更新模板

## 🔥 推荐：批量工作流（最新功能）

### ⭐ 方式 1：一键式完整工作流（最推荐）

**完全自动化**，一条命令搞定造表、完善元数据、生成测试文件：

```bash
cd scripts
python batch_workflow.py cjjcommon dataops_shitingjie --count 3
```

**自动执行**：
1. ✅ 创建 3 个测试表（自动生成表名）
2. ✅ 完善 3 个表的元数据
3. ✅ 生成批量上传文件（3 行数据）

**核心优势**：
- 🚀 **零手动干预**：全程自动化
- 📦 **真正的批量**：支持 1-3 个表（默认 1 个）
- ⚡ **一键完成**：从造表到生成文件
- 🎯 **表数量限制**：最多 3 个表，方便排查问题

📖 **详细文档**：[批量工作流快速参考](docs/批量工作流快速参考.md)

---

### 🔧 方式 2：模板更新器（已有表场景）

如果表已经存在并完成元数据完善，使用 **模板更新器** 快速生成测试文件：

**核心优势**：
- 🎯 **单一测试文件**：只保留模板和最新测试文件
- ⚡ **快速更新**：一条命令更新表信息和抽数配置
- 📦 **文件简洁**：不再每次测试都生成新文件
- 🔄 **支持多表**：可指定 1-3 个表

**快速使用**：

```bash
cd scripts

# 单表模式（默认）
python template_updater.py cjjcommon dataops_shitingjie test_table_01

# 批量模式（多表）
python template_updater.py cjjcommon dataops_shitingjie \
  test_table_01 test_table_02 test_table_03

# TiDB 环境
python template_updater.py tidb-ares ares test_tidb_table --db-type tidb
```

📖 **详细文档**：[模板更新器使用指南](docs/模板更新器使用指南.md)

---

## 📦 快速开始（传统方式）

### 方式 1：基于已有表生成

```bash
/jdbc-warehouse-test 为 stjtestadb.adb_json_batch_01 生成测试文件
```

### 方式 2：先造表再生成

```bash
/jdbc-warehouse-test 克隆 adb_json_batch_01 并生成测试文件
```

### 方式 3：生成异常场景

```bash
/jdbc-warehouse-test 为 test_table 生成字段缺失异常场景
```

## 🔧 脚本直接调用

### 基础用法

```bash
cd scripts
python index.py generate --database stjtestadb --table adb_json_batch_01
```

### 完整参数

```bash
python index.py generate \
  --database stjtestadb \
  --table adb_json_batch_01_0227 \
  --scenario success \
  --dbType adb
```

### 集成模式（先造表）

```bash
python index.py generate \
  --sourceTable adb_json_batch_01 \
  --env adb-realtime \
  --createTable \
  --scenario success
```

## 📋 参数说明

| 参数 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `--database` | 是 | 数据库名称 | `stjtestadb` |
| `--table` | 是 | 表名 | `adb_json_batch_01` |
| `--scenario` | 否 | 测试场景（默认 success） | `success`, `failed_F001` |
| `--dbType` | 否 | 数据源类型（自动推断） | `mysql`, `tidb`, `adb` |
| `--sourceTable` | 否 | 源表名（createTable 模式） | `adb_json_batch_01` |
| `--env` | 否 | 环境名（createTable 模式） | `adb-realtime` |
| `--createTable` | 否 | 是否先创建表 | 标志参数 |
| `--output` | 否 | 自定义输出路径 | `/custom/path/` |

## 🎬 支持的测试场景

### 成功场景

| 场景 ID | 场景名称 | 说明 |
|---------|---------|------|
| `success` | 标准成功 | 增量合并模式（默认） |
| `success_all` | 全量覆盖 | 全量覆盖模式 |
| `success_ins` | 增量分区 | 增量分区模式 |

### 异常场景

| 场景 ID | 场景名称 | 说明 |
|---------|---------|------|
| `failed_F001` | 字段缺失 | 缺少必需字段 |
| `failed_F002` | 字段格式错误 | 格式不符合规范 |
| `failed_F003` | 联动规则冲突 | 抽数/处理方式不匹配 |
| `failed_F004` | 元数据未完善 | 表未完善元数据 |

## 📁 文件输出

### 输出位置

```
JBDC入仓/BIZ_REQ_33706_001_批量入仓_新增任务/test_data/
```

### 文件命名规范

```
格式：batch_{场景}_{表名}_{时间戳}.xlsx

示例：
- batch_success_batch_test_warehouse_20260228104525.xlsx
- batch_failed_F001_test_table_20260227150315.xlsx
```

## 🗂️ 生成的文件结构

### 23 列字段清单

| 列号 | 字段名称 | 取值逻辑 | 示例 |
|------|---------|---------|------|
| 1 | 数据源类型 | 自动推断 | `mysql`, `adb`, `tidb` |
| 2 | 实例 | 从表信息获取 | `sitadbrealtimedw` |
| 3 | 库 | 从表信息获取 | `stjtestadb` |
| 4 | 表 | 从表信息获取 | `adb_json_batch_01` |
| 5 | 业务负责人 | 固定值 | `施婷杰` |
| 6 | 业务负责人UID | 固定值 | `71e8b23d-...` |
| 7 | 技术负责人 | 固定值 | `施婷杰` |
| 8 | 技术负责人UID | 固定值 | `71e8b23d-...` |
| 9 | 创建人 | 固定值 | `施婷杰` |
| 10 | 创建人UID | 固定值 | `71e8b23d-...` |
| 11 | 用户旅程节点 | 随机选择 | `风险审核` |
| 12 | 需求目的 | 固定值 | `自动化测试` |
| 13 | 抽数方式 | 场景决定 | `ins`, `all` |
| 14 | 处理方式 | 场景决定 | `merge`, `all`, `ins` |
| 15 | 调度周期 | 固定值 | `day` |
| 16 | 调度时间 | 随机生成 | `04:20` |
| 17 | CPU | 固定值 | `1` |
| 18 | 内存 | 固定值 | `2048` |
| 19 | 创建时间字段 | 默认值 | `created_at` |
| 20 | 更新时间字段 | 默认值 | `updated_at` |
| 21 | 批量条数 | 默认值 | `1024` |
| 22 | 抽数数据源 | 自动拼接 | `input_adb_sitadbrealtimedw_stjtestadb` |
| 23 | 抽数主键 | 默认值 | `id` |

## 🔗 工作流集成

### 完整工作流

```
1. 创建表
   /test-create-jdbctable 克隆 adb_json_batch_01

2. 完善元数据
   /metadata-complete stjtestadb.adb_json_batch_01_0227

3. 生成测试文件
   /jdbc-warehouse-test 为 stjtestadb.adb_json_batch_01_0227 生成测试文件

4. 调用接口测试
   POST /dataops/etlx/batch/v2/validate
```

### 一键式工作流

```
/jdbc-warehouse-test 克隆 adb_json_batch_01 并生成测试文件
```

自动执行：
1. ✅ 调用 test-table 克隆表
2. ✅ 调用 metadata-complete 完善元数据
3. ✅ 生成测试文件

## 📚 业务参考文档

此 skill 实现了 JDBC 批量入仓业务流程，详细的业务规范和接口定义请参考以下文档：

> ⚠️ **注意**：以下业务文档原存放在 `JBDC入仓/` 目录，已被删除。如需恢复，请从业务需求文档中获取。

### 核心业务指引
- [TKI_007: 批量入仓测试文件构建指引（已删除）](./SKILL.md) - ~~23列字段取值逻辑、联动规则~~

### 相关接口文档
- [TKI_003: 批量上传校验接口（已删除）](./SKILL.md) - ~~上传 Excel 文件并校验~~
- [TKI_004: 查询校验结果接口（已删除）](./SKILL.md) - ~~查询异步校验结果~~
- [TKI_005: 提交批量操作任务接口（已删除）](./SKILL.md) - ~~提交到 BPM 审批流程~~

### 数据表结构
- [TKD_006-TKD_009: 配置表结构（已删除）](./SKILL.md) - ~~流程实例表、抽数节点配置表等~~

### 业务规则
- [TKR_007: 批量入仓发布成功判断（已删除）](./SKILL.md) - ~~多表关联验证规则~~

> 💡 **说明**：业务文档已迁移到统一的业务需求管理目录。

## ⚙️ 配置说明

### 数据库连接配置

复��� test-table 的数据库配置：
```
scripts/db_config.ini
```

### 输出路径配置

```python
# scripts/config.py
DEFAULT_OUTPUT_DIR = "aitestrunner/skills/jdbc-warehouse-test/test_data"
```

### 固定值配置

```python
# scripts/config.py
FIXED_VALUES = {
    'person_name': '施婷杰',
    'person_uid': '71e8b23d-45e2-497a-b247-f5b807fb4f65',
    'purpose': '自动化测试',
    ...
}
```

## 🐛 常见问题

### Q1: 表不存在怎么办？

先使用 test-table skill 创建表，或使用集成模式：
```bash
/jdbc-warehouse-test 克隆 源表名 并生成测试文件
```

### Q2: 元数据未完善怎么办？

先使用 metadata-complete skill，或使用集成模式自动完善。

### Q3: 如何验证生成的文件？

1. 检查文件是否在 test_data 目录
2. 打开文件查看是否有 23 列
3. 验证字段值是否符合规范
4. 使用 validate 接口测试

### Q4: 如何添加新的异常场景？

1. 在 `references/scenarios/failed/` 创建新文档
2. 在 `scripts/xlsx_generator.py` 添加场景处理逻辑
3. 更新 `scripts/config.py` 的场景配置

## 📝 开发说明

### 目录结构

```
jdbc-warehouse-test/
├── SKILL.md                           # Skill 定义
├── README.md                          # 本文档
├── docs/                              # 使用文档
│   ├── 批量工作流快速参考.md          # ⭐ 批量工作流说明
│   ├── 模板更新器使用指南.md
│   └── 模板更新器快速参考.md
└── scripts/                           # 核心脚本
    ├── batch_workflow.py              # ⭐ 批量工作流（一键式，最推荐）
    ├── template_updater.py            # 模板更新器（支持多表）
    ├── index.py                       # 入口（生成器模式）
    ├── batch_upload_validate.py      # 上传校验接口调用
    ├── batch_query_result.py          # 查询结果接口调用
    ├── batch_submit_task.py           # 提交任务接口调用
    ├── xlsx_generator.py              # XLSX 生成核心
    ├── table_reader.py                # 表结构读取
    ├── config.py                      # 配置管理
    ├── api_config.py                  # API 配置
    └── db_config.ini                  # 数据库配置
```

### 核心模块

**批量工作流（最推荐）**：
- **batch_workflow.py**: 一键式完整工作流，自动执行造表→完善元数据→生成测试文件
  - 支持 1-3 个表的批量处理
  - 自动生成表名（带时间戳）
  - 交互式确认和错误处理

**模板更新器（已有表场景）**：
- **template_updater.py**: 基于固定模板快速生成测试文件
  - 支持单表或多表模式（1-3 个表）
  - 避免文件爆炸
  - 适用于表已存在的场景

**生成器模式（传统）**：
- **index.py**: 参数解析、流程控制
- **xlsx_generator.py**: XLSX 文件生成核心逻辑
- **table_reader.py**: 数据库连接、表结构读取
- **config.py**: 配置管理、默认值定义

**接口调用**：
- **batch_upload_validate.py**: TKI_003 批量上传校验
- **batch_query_result.py**: TKI_004 查询校验结果
- **batch_submit_task.py**: TKI_005 提交批量任务
- **api_config.py**: 接口域名和路径配置

## 🚀 功能状态

### ✅ 已实现
- [x] **批量工作流**（一键式完整流程，支持 1-3 个表）
- [x] **模板更新器**（支持多表，避免文件爆炸）
- [x] 基于已有表生成测试文件
- [x] 集成 test-table 和 metadata-complete
- [x] 支持多种测试场景（成功/失败）
- [x] 支持 MySQL/TiDB/ADB 数据源
- [x] 批量接口调用脚本（上传/查询/提交）
- [x] API 配置管理
- [x] 自动表名生成（带时间戳）
- [x] 表数量限制（最多 3 个）

### 🔮 未来扩展
- [ ] 支持自定义字段值
- [ ] 支持更多异常场景
- [ ] 支持测试数据预览
- [ ] 支持从 Excel 模板导入配置
- [ ] 支持批量删除测试表

## 📮 联系与反馈

如有问题或建议，请反馈给 Claude Code 或项目维护者。
