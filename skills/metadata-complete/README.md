# 元数据完整性管理工具

MySQL 库表元数据完整性管理自动化工具，串联调用 GET 和 POST 接口完成元数据查询、字段补充和管理操作。

## 功能特性

- 🔍 **自动查询**：调用 GET 接口获取库表元数据
- ✨ **智能补充**：自动补充 5 个必需字段属性
- 🚀 **自动管理**：调用 POST 接口完成元数据管理
- 🎯 **自然语言**：支持自然语言描述，无需记忆参数
- 🔧 **灵活配置**：支持自定义更新/删除权限

## 补充的字段

自动为每个字段补充以下属性（默认值均为 false）：

- `canNotBeModified` - 字段是否不可修改
- `columnEditing` - 字段是否可编辑
- `sensitive` - 字段是否敏感
- `json` - 字段是否为 JSON 类型
- `enumerated` - 字段是否为枚举类型

## 使用方式

���工具提供三种使用方式，推荐使用自然语言方式，最简单直观。

### 方式一：自然语言（推荐）

在 Claude Code 中直接用自然语言描述需求。

**命令格式：**
```
/metadata-complete [你的需求描述]
```

**使用示例：**

1. **使用 "库.表" 格式：**
```
/metadata-complete 帮我管理 dataops_shitingjie.user_info 表的元数据
```

2. **指定实例：**
```
/metadata-complete 补充 cjjcommon 的 dataops.test_table 元数据
```

3. **临时表（支持删除）：**
```
/metadata-complete 管理 temp_table 的元数据，这是临时表需要支持删除
```

4. **简洁描述：**
```
帮我管理 cjjcommon.dataops_shitingjie.user_info 的元数据
```

**优势：**
- ✅ 无需记忆参数格式
- ✅ 自动识别实例、数据库、表名
- ✅ 自动识别权限设置
- ✅ 只在必要时询问缺失参数

### 方式二：标准参数调用

使用标准参数格式，适合精确控制。

**基础命令：**
```bash
/metadata-complete --instance cjjcommon --database dataops_shitingjie --table your_table
```

**完整命令：**
```bash
/metadata-complete \
  --instance cjjcommon \
  --database dataops_shitingjie \
  --table your_table \
  --existUpdate true \
  --existDelete false
```

### 方式三：独立运行脚本

适合需要集成到自动化流程中的场景。

```bash
cd metadata-complete/scripts
python index.py --instance cjjcommon --database dataops_shitingjie --table your_table
```

## 参数说明

### 必需参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--instance` | MySQL 实例标识 | `cjjcommon` |
| `--database` | 数据库名称 | `dataops_shitingjie` |
| `--table` | 数据表名称 | `user_info` |

### 可选参数

| 参数 | 说明 | 默认值 | 可选值 |
|------|------|--------|--------|
| `--existUpdate` | 是否支持更新 | `true` | `true`, `false` |
| `--existDelete` | 是否支持删除 | `false` | `true`, `false` |

### 固定参数（无需指定）

- **人员名称 (p_n)**: 施婷杰
- **人员 UUID (p_u)**: 71e8b23d-45e2-497a-b247-f5b807fb4f65

## 常用实例

| 实例 | 常用数据库 | 说明 |
|------|-----------|------|
| cjjcommon | dataops_shitingjie | 常用测试库 |
| bigdata-biz | dataops, datagovernor | 大数据业务库 |
| cjjloan | datahub | 贷款业务库 |

## 使用场景

### 场景 1：普通业务表（默认）

```bash
/metadata-complete --instance cjjcommon --database dataops_shitingjie --table user_info
```

**效果：**
- ✅ 支持更新操作
- ❌ 不支持删除操作（安全）

### 场景 2：临时表（支持删除）

```bash
/metadata-complete \
  --instance cjjcommon \
  --database dataops_shitingjie \
  --table temp_cache_table \
  --existDelete true
```

**效果：**
- ✅ 支持更新操作
- ✅ 支持删除操作

### 场景 3：只读表（历史数据）

```bash
/metadata-complete \
  --instance cjjcommon \
  --database dataops_shitingjie \
  --table history_archive \
  --existUpdate false
```

**效果：**
- ❌ 不支持更新操作
- ❌ 不支持删除操作

## 执行流程

```
1. 查询元数据 (GET)
   ↓
2. 补充字段属性
   ↓
3. 提交管理 (POST)
   ↓
4. 返回结果
```

## 输出示例

### 成功执行

```
======================================================================
元数据完整性管理 Skill
======================================================================
实例: cjjcommon
数据库: dataops_shitingjie
表: user_info
人员: 施婷杰
更新操作: 支持
删除操作: 不支持
======================================================================

============================================================
开始执行元数据完整性管理流程
============================================================
[GET] 正在查询元数据...
[GET] 成功获取元数据
------------------------------------------------------------
[处理] 已为 12 个字段补充固定属性
------------------------------------------------------------
[POST] 正在管理元数据...
[POST] 元数据管理成功
============================================================
元数据完整性管理流程执行成功！
============================================================

======================================================================
✓ Skill 执行成功！
======================================================================
```

## 其他工具脚本

在 `scripts/` 目录下提供了额外的工具：

### 1. 快速执行脚本

适合快速测试单个表，修改配置参数后直接运行 `metadata_complete.py`。

### 2. 批量处理脚本

```bash
cd scripts
python batch_process.py
```

适合批量处理多个表的元数据管理。

## 测试验证

使用测试表验证功能：

```bash
# 测试 1：默认参数
python index.py --instance cjjcommon --database dataops_shitingjie --table 0418bugfuxianccc

# 测试 2：支持删除
python index.py --instance cjjcommon --database dataops_shitingjie --table 0418bugfuxianccc --existDelete true

# 测试 3：只读模式
python index.py --instance cjjcommon --database dataops_shitingjie --table 0418bugfuxianccc --existUpdate false
```

**注意**：测试前先进入 scripts 目录：
```bash
cd metadata-complete/scripts
```

## 详细文档

- [SKILL.md](SKILL.md) - 完整功能文档和自然语言使用指南
- [API_information.md](references/API_information.md) - API 接口详细说明

## 技术细节

### 接口调用链路

```
metadata-complete/
    ↓
scripts/index.py (Skill 入口)
    ↓
MetadataCompleteManager
    ↓
GET /firekylin/mysql-metadata/mysql/table/metadata
    ↓
补充 columnMetadata 字段
    ↓
POST /firekylin/mysql-metadata/mysql/table/metadata:manage
    ↓
返回执行结果
```

### 环境配置

- **部署环境**: SIT03
- **基础 URL**: http://firekylin.apps01.ali-bj-sit03.shuheo.net
- **Python 版本**: 3.6+
- **依赖**: requests

## 常见问题

**Q: 如何在 Claude Code 中调用这个 Skill？**

A: 在 Claude Code 对话中直接输入：
```
/metadata-complete --instance cjjcommon --database dataops_shitingjie --table your_table
```
或使用自然语言：
```
/metadata-complete 帮我管理 dataops_shitingjie.user_info 表的元数据
```

**Q: 可以不指定 existUpdate 和 existDelete 吗？**

A: 可以，默认值为：
- existUpdate = true（支持更新）
- existDelete = false（不支持删除）

**Q: 人员信息可以修改吗？**

A: 人员信息已固定为施婷杰，无需也无法在命令行修改。如需修改，需要编辑 `index.py` 文件。

**Q: 如何测试 Skill 是否正常工作？**

A: 使用测试表运行：
```bash
/metadata-complete --instance cjjcommon --database dataops_shitingjie --table 0418bugfuxianccc
```

**Q: Skill 执行失败怎么办？**

A: 检查以下事项：
1. 网络是否可以访问 SIT03 环境
2. 实例、数据库、表名称是否正确
3. 查看详细错误日志

**Q: 如何批量处理多个表？**

A: 使用批量处理脚本：
```bash
cd scripts
python batch_process.py
```

## 注意事项

1. 需要访问 SIT03 环境网络
2. 确认实例、数据库、���名称正确
3. 人员信息已固定为施婷杰
4. 默认支持更新，不支持删除
5. 临时表建议开启删除权限

## 版本信息

- **版本**: 1.0.0
- **更新日期**: 2026-02-11
- **环境**: SIT03 (http://firekylin.apps01.ali-bj-sit03.shuheo.net)
- **状态**: ✅ 已测试，可用
