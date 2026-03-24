# Prompt 对比分析文档

## 概述

本文档对比分析 AITestRunner 项目中两套 Prompt 体系：
1. **项目级 Prompt** (`aitestrunner/prompt/prompt_case_gen.user.md`) - 通用模板
2. **需求级 Prompt** (`TDD/REQ-33706-JDBC批量入仓/prompt_case_gen.user.md`) - 定制化配置

---

## 一、Prompt 定位对比

| 维度 | 项目级 Prompt | 需求级 Prompt (JDBC入仓) |
|------|---------------|--------------------------|
| **文件位置** | `aitestrunner/prompt/prompt_case_gen.user.md` | `TDD/REQ-33706-JDBC批量入仓/prompt_case_gen.user.md` |
| **定位** | 通用模板，适用于所有项目 | 特定需求的定制化 Prompt |
| **内容** | AI剧本生成接口示例（通用例子） | 针对批量入仓接口的专门指令 |
| **特点** | 侧重通用的测试用例设计策略 | 包含 Skill 生成前置条件的详细说明 |

---

## 二、核心功能对比

### 2.1 前置条件处理

| 项目级 Prompt | 需求级 Prompt (JDBC入仓) |
|---------------|--------------------------|
| 简单的通用示例 | 详细的接口类型分类说明 |
| 无 | **文件上传类**、**查询类**、**业务操作类** 三种类型区分 |

**需求级 Prompt 独有内容**：

```yaml
#### 类型1：文件上传类接口（如 batch_upload_validate）
- **前置条件**：使用 skill 自动生成测试 Excel 文件
- **示例**：
preconditions:
  - intent: "前置1：生成测试Excel文件"
    action: "skill"
    params:
      描述: "为批量入仓接口生成测试Excel，success场景"
```

### 2.2 Skill 集成

| 项目级 Prompt | 需求级 Prompt (JDBC入仓) |
|---------------|--------------------------|
| 无相关说明 | 明确指定使用 skill 生成测试文件 |
| 无 | 框架会自动解析自然语言并调用对应的 Skill |

### 2.3 文件路径规范

| 项目级 Prompt | 需求级 Prompt (JDBC入仓) |
|---------------|--------------------------|
| 无 | 指定文件路径：`/test_excel/batch_test_latest.xlsx` |

### 2.4 数据清理策略

| 项目级 Prompt | 需求级 Prompt (JDBC入仓) |
|---------------|--------------------------|
| 无相关说明 | **严禁每个用例都添加 database_delete 清理历史数据** |
| 无 | **绝对禁止添加前置清理步骤** |
| 无 | 测试数据应使用动态唯一标识符（UUID、时间戳）避免冲突 |

---

## 三、需求级 Prompt 独有内容详解

### 3.1 Skill 生成前置条件

```yaml
preconditions:
  - intent: "前置1：生成测试Excel文件"
    action: "skill"
    params:
      描述: "为批量入仓接口生成测试Excel，success场景"
```

**说明**：
- 只需要描述业务需求，框架会自动调用 LLM 解析意图
- 自动选择合适的 Skill 执行
- 文件路径使用 `/test_excel/batch_test_latest.xlsx`

### 3.2 异步校验设计

- **实时与终态校验**：每个用例必须包含对核心执行结果的校验
- **数据库字段终态**：必须使用 `assert_database_field` 验证业务执行后数据库字段的最终业务状态
- **轮询断言**：针对异步落库链路，必须包含 `timeout` 轮询断言

### 3.3 禁止事项

- ❌ **严禁每个用例都添加 database_delete 清理历史数据**
- ❌ **绝对禁止添加前置清理步骤**
- ❌ 即使同一用户的测试数据也不需要清理

### 3.4 数据构造原则

- ✅ 测试数据应使用**动态唯一标识符**（UUID、时间戳）避免冲突
- ✅ 前置条件只需要 **skill 生成文件**即可，不需要任何数据库操作

---

## 四、整合建议

### 4.1 为什么需要整合？

项目级 Prompt 是**通用模板**，需求级 Prompt 是**针对特定需求的增强配置**。将需求级 Prompt 中的 Skill 相关内容整合到项目级模板中，可以实现：

1. 所有项目都能使用 Skill 自动生成测试数据
2. 减少重复配置工作
3. 统一测试用例生成规范

### 4.2 整合方案

建议在项目级 `prompt_case_gen.user.md` 中新增以下章节：

```markdown
## 前置条件规范

### A. 接口类型与前置条件映射

不同类型的接口需要不同的前置条件，请根据目标接口类型选择正确的 precondition：

#### 类型1：文件上传类接口
- **前置条件**：使用 skill 自动生成测试文件
- **示例**：
  ```yaml
  preconditions:
    - intent: "前置1：生成测试文件"
      action: "skill"
      params:
        描述: "为XX接口生成测试数据，success场景"
  ```

#### 类型2：查询类接口
- **前置条件**：先调用上游接口获取必要参数

#### 类型3：业务操作类接口
- **前置条件**：确保前置状态满足业务规则

### B. Skill 自动化

- Skill 会自动解析自然语言并调用对应的 Skill 脚本
- 生成的文件路径会自动注入 context 供后续步骤使用
- 可用变量：`${context.skill.file_path}`

### C. 数据清理规范

- **禁止**：每个用例都添加 database_delete 清理历史数据
- **禁止**：添加前置清理步骤
- **推荐**：使用动态唯一标识符（UUID、时间戳）避免数据冲突

---

## 五、相关文件索引

| 文件 | 说明 |
|------|------|
| `aitestrunner/prompt/prompt_case_gen.user.md` | 项目级用户 Prompt（通用模板） |
| `aitestrunner/prompt/prompt_case_gen.system.md` | 项目级系统 Prompt |
| `TDD/REQ-33706-JDBC批量入仓/prompt_case_gen.user.md` | JDBC入仓需求级用户 Prompt |
| `aitestrunner/actions/generic/skill.py` | Skill 动作实现 |
| `aitestrunner/actions/generic/bridge_skill.py` | Skill 桥接实现 |
| `aitestrunner/skills/SKILL_ARCHITECTURE.md` | Skill 架构文档 |
