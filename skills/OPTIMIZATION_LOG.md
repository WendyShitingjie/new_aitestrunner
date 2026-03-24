# Skills 优化改进记录

---

## 改进日期: 2026-03-23

### 1. Skill 自动发现机制

**问题**：之前 skill 和 action 是硬编码的，新增 skill 需要手动修改代码

**解决方案**：
- 实现 `skill_discoverer.py` 自动扫描 skills 目录
- 新增 skill 目录后自动被发现，无需改代码

**新增文件**：`actions/skill_discoverer.py`

---

### 2. 异常场景配置化

**问题**：`TC_005 (failed_F004)` 期望 `VALIDATE_FAILED`，实际 `VALIDATE_SUCCESS`

**解决方案**：
- 创建 `scenario_config.json` 配置化管理异常场景
- 修改 `config.py` 添加 `get_scenario_config()`、`is_skip_metadata()` 等函数
- 修改 `xlsx_generator.py` 从配置读取异常处理逻辑
- 修改 `batch_workflow.py` 使用配置判断是否跳过元数据完善

**新增文件**：`skills/jdbc-warehouse-test/scripts/scenario_config.json`

**修改文件**：
- `skills/jdbc-warehouse-test/scripts/config.py`
- `skills/jdbc-warehouse-test/scripts/xlsx_generator.py`
- `skills/jdbc-warehouse-test/scripts/batch_workflow.py`

**测试结果**：5/5 通过 ✅

---

## 改进日期: 2026-02-27

### 1. test-create-jdbctable Skill - 自动生成目标表名

**问题**：使用 `copy-table` 命令时需要手动指定目标表名

**解决方案**：`--targetTable` 参数改为可选，不提供时自动生成 `源表名_MMDD_序号`

---

### 2. metadata-complete Skill - 自动推断实例名

**问题**：每次都需要同时提供实例名和数据库名

**解决方案**：建立数据库名到实例名映射表，不提供实例名时自动推断
