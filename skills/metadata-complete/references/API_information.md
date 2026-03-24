# MySQL库表元数据相关接口串联调用API说明文档

 **文档说明**：本文档说明MySQL库表元数据两个接口的串联调用核心逻辑，明确调用顺序、参数传递规则及使用流程。

 **统一部署域名**：http://firekylin.apps01.ali-bj-sit03.shuheo.net

 ---

 ## 一、接口核心概述

 ### 接口依赖关系

 两个接口为依赖关系：**先调用GET接口查询元数据，再用POST接口进行元数据管理**，POST核心参数均来自GET接口响应。

 ### 接口分工

 | 接口类型 | 接口地址 | 核心功能 | 串联角色 |
 |---------|---------|---------|---------|
 | GET请求 | /firekylin/mysql-metadata/mysql/table/metadata | 查询库表完整元数据 | 前置接口，提供POST所需参数 |
 | POST请求 | /firekylin/mysql-metadata/mysql/table/metadata:manage | 管理库表元数据 | 后置接口，依赖GET接口，无法独立调用 |

 ---

 ## 二、前置接口（GET）核心说明

 ### 2.1 基础信息

 - **接口地址**：GET http://firekylin.apps01.ali-bj-sit03.shuheo.net/firekylin/mysql-metadata/mysql/table/metadata
 - **接口状态**：已上线（V2.0）
 - **数据格式**：application/json

 ### 2.2 核心请求参数（Query，必传）

 | 参数名      | 类型     | 描述        | 与POST关联               |
 |----------|--------|-----------|-----------------------|
 | instance | string | MySQL实例标识 | 与POST Query参数完全一致     |
 | database | string | 数据库名称     | 与POST Query参数完全一致     |
 | table    | string | 数据表名称     | 对应POST Body的tableName |
 | p_n      | string | 人员名称      | 与POST Query参数完全一致     |
 | p_u      | string | 人员唯一标识    | 与POST Query参数完全一致     |

 ### 2.3 核心响应参数（POST参数来源）

 **说明**：状态码200返回，核心参数需完整提取传递至POST接口。

 | GET响应参数 | 类型 | 对应POST参数 | 传递要求 |
 |------------|------|-------------|---------|
 | tableName | string | Body → tableName | 必传，值不变 |
 | existUpdate | boolean | Body → existUpdate | 必传，按实际操作设置 |
 | existDelete | boolean | Body → existDelete | 必传，按实际操作设置 |
 | columnMetadata | array | Body → columnMetadata | 必传，需补充5个固定字段 |

 #### 2.3.1 columnMetadata补充规则

 **重要**：需补充5个固定默认字段，原有字段不变：

 - `canNotBeModified: false`
 - `columnEditing: false`
 - `sensitive: false`
 - `json: false`
 - `enumerated: false`

 ---

 ## 三、后置接口（POST）核心说明

 ### 3.1 基础信息

 - **接口地址**：POST http://firekylin.apps01.ali-bj-sit03.shuheo.net/firekylin/mysql-metadata/mysql/table/metadata:manage
 - **接口状态**：已上线（V2.0）
 - **请求格式**：application/json

 ### 3.2 核心请求参数

 #### 3.2.1 Query参数（复用GET，必传）

 **说明**：instance、database、p_n、p_u，与GET接口完全一致，不可修改。

 #### 3.2.2 Body核心参数（必传）

 | POST参数 | 类型 | 参数来源 | 传递要求 |
 |---------|------|---------|---------|
 | tableName | string | GET响应tableName | 不可修改 |
 | existUpdate | boolean | 参考GET响应 | 按实际操作设置 |
 | existDelete | boolean | 参考GET响应 | 按实际操作设置 |
 | columnMetadata | array | GET响应+补充字段 | 完整传递，不可遗漏 |

 ---

 ## 四、串联调用流程及核心规则

 ### 4.1 固定调用顺序

 1. **调用GET接口**
    - 传入5个Query参数（instance、database、table、p_n、p_u）
    - 提取tableName、columnMetadata等核心响应参数

 2. **解析GET响应**
    - 补充columnMetadata的5个固定字段
    - 组装POST的Query和Body参数

 3. **调用POST接口**
    - 传入参数，完成元数据管理操作

 ### 4.2 核心规则（必守）

 1. **Query参数一致性**：POST的Query参数与GET完全一致，不可修改
 2. **Body参数来源性**：POST的Body核心参数均来自GET响应，不可随意修改原有字段值
 3. **表标识一致性**：两个接口的instance、database、表名需完全一致，避免操作错误

 ### 4.3 常见问题

 **参数错误**
 - 检查Query参数一致性
 - 检查Body核心参数完整性
 - 检查columnMetadata补充字段

 **无响应**
 - 确认GET调用成功
 - 确认POST请求格式为application/json
 - 确认参数格式正确

 ---

 ## 五、总结

 两个接口为"查询-管理"依赖关系，串联核心是"参数复用+按需补充"。

 **关键要点**：
 - 严格遵循调用顺序
 - 严格遵循参数规则
 - 确保参数完整性和一致性

 通过遵循以上规则，即可实现自动化串联调用，确保接口调用成功。

 ---

 ## 附录：完整调用示例

 ### 步骤1：调用GET接口

 ```http
 GET http://firekylin.apps01.ali-bj-sit03.shuheo.net/firekylin/mysql-metadata/mysql/table/metadata?instance=xxx&database=xxx&table=xxx&p_n=xxx&p_u=xxx
 ```

 ### 步骤2：解析GET响应并补充字段

 ```json
 {
   "tableName": "从GET响应获取",
   "existUpdate": true/false,
   "existDelete": true/false,
   "columnMetadata": [
     {
       // GET响应的原有字段...
       "canNotBeModified": false,
       "columnEditing": false,
       "sensitive": false,
       "json": false,
       "enumerated": false
     }
   ]
 }
 ```

 ### 步骤3：调用POST接口

 ```http
 POST http://firekylin.apps01.ali-bj-sit03.shuheo.net/firekylin/mysql-metadata/mysql/table/metadata:manage?instance=xxx&database=xxx&p_n=xxx&p_u=xxx
 Content-Type: application/json

 {
   "tableName": "从GET响应获取的值",
   "existUpdate": true/false,
   "existDelete": true/false,
   "columnMetadata": [补充后的完整数组]
 }
 ```

 ---

 **文档版本**：V2.0
 **最后更新**：基于wiki页面ID 418156055生成
 **生成时间**：2026-02-10
