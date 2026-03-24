# SQL验证规则列表

| 规则代码 | 规则名称 | 规则类型 | 状态 |
|---------|---------|---------|------|
| DROP_TRUNCATE_RULE | 执行drop、truncate 表名后缀应该为_fordrop_yyyyMMdd | EXE_CHECK | 1 |
| COLUMN_TYPE_ERROR | 字段类型禁止策略 | COLUMN_CHECK | 1 |
| CREATE_TABLE_COLUMN_CHARSET_COLLAT_FORBID | 建表语句中字段不允许指定字符集和排序规则 | COLUMN_CHECK | 1 |
| UPDATED_AT_MUST_HAVE_INDEX | 更新时间需要有索引 | TABLE_CHECK | 1 |
| RENAME_TABLE_RISK | 表重命名风险 | EXE_CHECK | 1 |
| DROP_TRANCATE_RISK | 执行drop、truncate，默认为高风险 | EXE_CHECK | 1 |
| UPDATED_AT_NEED_EXTRA | update_at 建议设置为时间自动更新 | COLUMN_CHECK | 1 |
| CREATE_UPDATE_AT_DEFAULT_VALUE | created_at,updated_at默认值建议 | COLUMN_CHECK | 1 |
| ZEROFILL_FORBID | 字段禁用zerofill属性 | COLUMN_CHECK | 1 |
| PK_MUST_BE_INCREMENT | 限制主键列必须自增 | COLUMN_CHECK | 1 |
| INCREMENT_MUST_BE_UNSIGNED | 限制自增列为无符号 | COLUMN_CHECK | 1 |
| INCREMENT_MUST_BE_ID | 限制自增列名字为id | COLUMN_CHECK | 1 |
| COLUMN_NAME_KEY_WORD | 字段名不能是关键字 | COLUMN_CHECK | 1 |
| TABLE_NAME_KEY_WORD | 表名不能是关键字 | TABLE_CHECK | 1 |
| CHECK_TABLE_CHARSET | 限制表字符集 | TABLE_CHECK | 1 |
| CHECK_COLUMN_EXIST | 新建表，校验某些字段是否存在 | TABLE_CHECK | 1 |
| COLUMN_TYPE_WARNING | 字段允许的类型 | COLUMN_CHECK | 1 |
| DROP_INDEX_RISK | 删除索引风险 | INDEX_CHECK | 1 |
| DROP_PK_RISK | 删除主键风险 | INDEX_CHECK | 1 |
| RENAME_COLUMN_RISK | 字段重命名风险 | COLUMN_CHECK | 1 |
| DROP_COLUMN_RISK | 删除字段风险 | COLUMN_CHECK | 1 |
| INDEX_TOTAL_RISK | 控制表索引总数量风险 | TABLE_CHECK | 1 |
| NO_PK_RISK | 新建表，无主键风险 | TABLE_CHECK | 1 |
| INDEX_COLUMN_TOTAL | 限制新增索引字段个数 | INDEX_CHECK | 1 |
| PRYMARY_COLUMN_NAME_MUST_BE_ID | 主键名称必须命名为id | COLUMN_CHECK | 1 |
| PRYMARY_COLUMN_TYPE_MUST_BE_BIGINT | 主键类型必须是bigint | COLUMN_CHECK | 1 |
| PRYMARY_COLUMN_TOTAL | 限制新增主键字段个数 | INDEX_CHECK | 1 |
| INDEX_NAME_LOWER_CASE | 新增索引，限制索引名大小写 | INDEX_CHECK | 1 |
| COLUMN_NAME_LOWER_CASE | 新增字段，限制字段名大小写 | COLUMN_CHECK | 1 |
| TABLE_MUST_HAVE_PK | 新建表，必须要有主键(PK) | TABLE_CHECK | 1 |
| TABLE_NAME_LOWER_CASE | 新建表，限制表名全部小写 | TABLE_CHECK | 1 |
| NORMAL_INDEX_NAMING_RULE | 新增索引，限制Normal索引名格式 | INDEX_CHECK | 1 |
| UNIQUE_INDEX_NAMING_RULE | 新增索引，限制Unique索引名格式 | INDEX_CHECK | 1 |
| COLUMN_NAMING_PATITION_FORBID | 不能使用hive dataphin 分区字段ds或day作为字段名 | COLUMN_CHECK | 1 |
| CREATE_UPDATE_AT_NEED_DEFAULT | created_at,updated_at应该有默认值 | COLUMN_CHECK | 1 |
| COLUMN_NAMING_RULE | 列名使用小写字符、数字、下划线命名，不能以数字开头 | COLUMN_CHECK | 1 |
| COLUMN_COMMENT_CONTAINS_SPECIAL_CHARACTER | 列注释不能含有引号等特殊字符 | COLUMN_CHECK | 1 |
| COLUMN_COMMENT_MUST_NOT_SAME_WITH_COLUMN_NAME | 列注释不能与列名一致 | COLUMN_CHECK | 1 |
| COLUMN_COMMENT_CHINESE_LENGTH | 列注释中文字符数大于等于2 | COLUMN_CHECK | 1 |
| COLUMN_COMMENT_LENGTH | 列注释字符数大于等于2 | COLUMN_CHECK | 1 |
| COLUMN_MUST_HAVE_COMMENT | 列必须有列注释 | COLUMN_CHECK | 1 |
| TABLE_NAMING_RULE | 表名使用小写字符、数字、下划线命名，不能以数字开头 | TABLE_CHECK | 1 |
| TABLE_COMMENT_CONTAINS_SPECIAL_CHARACTER | 表注释不能含有引号等特殊字符 | TABLE_CHECK | 1 |
| TABLE_COMMENT_MUST_NOT_SAME_WITH_TABLE_NAME | 表注释不能与表名一致 | TABLE_CHECK | 1 |
| TABLE_COMMENT_CHINESE_LENGTH | 表注释中文字符数 | TABLE_CHECK | 1 |
| TABLE_COMMENT_LENGTH | 表注释字符数大于 | TABLE_CHECK | 1 |
| TABLE_MUST_HAVE_COMMENT | 表必须有表注释 | TABLE_CHECK | 1 |