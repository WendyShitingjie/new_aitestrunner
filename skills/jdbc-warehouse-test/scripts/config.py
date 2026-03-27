#!/usr/bin/env python3
"""
JDBC Warehouse Test Skill - 配置管理
"""
import os
import json
from pathlib import Path
from datetime import datetime

# ============= 加载场景配置 =============
_config_dir = Path(__file__).parent
_config_file = _config_dir / "scenario_config.json"

def _load_scenario_config():
    """加载场景配置文件"""
    if _config_file.exists():
        with open(_config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

SCENARIO_CONFIG = _load_scenario_config()

# ============= 输出路径配置 =============
# 默认输出目录（相对于 skill 目录）
DEFAULT_OUTPUT_DIR = "test_excel"

def get_output_path(custom_path=None):
    """
    获取输出路径（绝对路径）

    Args:
        custom_path: 自定义路径（可选）

    Returns:
        绝对路径
    """
    if custom_path:
        return os.path.abspath(custom_path)

    # 从 scripts/config.py 向上1层到 skill 目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    return os.path.join(project_root, DEFAULT_OUTPUT_DIR)


def get_relative_output_path():
    """
    获取输出路径（相对于 skills 目录）

    Returns:
        相对路径，如 skills/jdbc-warehouse-test/test_excel
    """
    # 获取 skill 名称
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_dir = os.path.dirname(script_dir)  # skill 目录
    skill_name = os.path.basename(skill_dir)
    
    # 返回相对于 skills 的路径
    return os.path.join("skills", skill_name, DEFAULT_OUTPUT_DIR)


# ============= 文件命名配置 =============
def generate_filename(scenario, table_name, timestamp=None):
    """
    生成文件名

    Args:
        scenario: 场景类型（success, failed_F001等）
        table_name: 表名
        timestamp: 时间戳（可选，默认当前时间）

    Returns:
        文件名
    """
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    return f"batch_{scenario}_{table_name}_{timestamp}.xlsx"


# 测试场景类型（从配置文件加载）
_scenarios_from_config = SCENARIO_CONFIG.get('scenarios', {})
SCENARIOS = {
    k: v.get('description', '') for k, v in _scenarios_from_config.items()
}

# 如果配置文件不存在，使用默认值
if not SCENARIOS:
    SCENARIOS = {
        'success': '成功场景-增量合并',
        'success_all': '成功场景-全量覆盖',
        'success_ins': '成功场景-增量分区',
        'failed_F001': '异常场景-字段缺失',
        'failed_F002': '异常场景-字段格式错误',
        'failed_F003': '异常场景-联动规则冲突',
        'failed_F004': '异常场景-元数据未完善'
    }


def get_scenario_config(scenario: str) -> dict:
    """获取指定场景的配置"""
    return _scenarios_from_config.get(scenario, {})


def get_extract_process(scenario: str) -> tuple:
    """获取抽数/处理方式
    
    Returns:
        (extract, process): 抽数方式, 处理方式
    """
    config = get_scenario_config(scenario)
    return config.get('extract'), config.get('process')


def is_skip_metadata(scenario: str) -> bool:
    """是否跳过元数据完善"""
    config = get_scenario_config(scenario)
    return config.get('skip_metadata', False)


# ============= 固定值配置 =============
FIXED_VALUES = {
    # 人员信息
    'person_name': '施婷杰',
    'person_uid': '71e8b23d-45e2-497a-b247-f5b807fb4f65',

    # 任务配置
    'purpose': '自动化测试',
    'schedule_cycle': 'day',
    'cpu': '1',
    'memory': '2048',
    'batch_size': '1024',

    # 字段默认值
    'primary_key': 'id',
    'created_field': 'created_at',
    'updated_field': 'updated_at'
}


# ============= 数据源类型映射 =============
DB_TYPE_MAPPING = {
    'mysql': 'mysql',
    'tidb': 'tidb',
    'adb': 'adb'
}

# 根据数据库名自动推断数据源类型
DB_NAME_TO_TYPE = {
    'stjtestadb': 'adb',
    'ares': 'tidb',
    'dataops_shitingjie': 'mysql',
    'dataops': 'mysql',
    'datagovernor': 'mysql',
    'datahub': 'mysql'
}


# ============= 实例名映射 =============
# 数据库名到实例名的映射（复用 metadata-complete 的逻辑）
DATABASE_TO_INSTANCE_MAP = {
    'dataops_shitingjie': 'cjjcommon',
    'dataops': 'bigdata-biz',
    'datagovernor': 'bigdata-biz',
    'datahub': 'cjjloan',
    'stjtestadb': 'sitadbrealtimedw',
    'ares': 'tidb-ares',
}


# ============= 抽数/处理方式联动规则 =============
# 格式：{场景类型: {'extract': 抽数方式, 'process': 处理方式}}
EXTRACT_PROCESS_RULES = {
    'success': {
        'extract': 'ins',
        'process': 'merge',
        'description': '增量合并模式（默认）'
    },
    'success_all': {
        'extract': 'all',
        'process': 'all',
        'description': '全量覆盖模式'
    },
    'success_ins': {
        'extract': 'ins',
        'process': 'ins',
        'description': '增量分区模式'
    },
    'failed_F003': {
        'extract': 'all',
        'process': 'merge',  # 故意错误：all 不能配 merge
        'description': '联动规则冲突'
    },
    'failed_F004': {
        'extract': 'ins',
        'process': 'merge',
        'description': '元数据未完善（数据正常，但表未完善元数据）'
    }
}


# ============= 用户旅程节点 =============
USER_JOURNEY_NODES = [
    '曝光',
    '点击',
    '注册',
    '登录',
    '进件',
    '授信',
    '借款',
    '还款',
    '风险审核',
    '客户服务',
    '营销活动'
]


# ============= 调度时间范围 =============
# 生成随机调度时间的范围
SCHEDULE_TIME_RANGE = {
    'hour_start': 0,    # 开始小时
    'hour_end': 23,     # 结束小时
    'minute_step': 5    # 分钟步长（5分钟间隔）
}


# ============= Excel 列头定义 =============
EXCEL_HEADERS = [
    '数据源类型',      # 1
    '实例',           # 2
    '库',             # 3
    '表',             # 4
    '业务负责人',      # 5
    '业务负责人UID',   # 6
    '技术负责人',      # 7
    '技术负责人UID',   # 8
    '创建人',          # 9
    '创建人UID',       # 10
    '用户旅程节点',    # 11
    '需求目的',        # 12
    '抽数方式',        # 13
    '处理方式',        # 14
    '调度周期',        # 15
    '调度时间',        # 16
    'CPU',            # 17
    '内存',            # 18
    '创建时间字段',    # 19
    '更新时间字段',    # 20
    '批量条数',        # 21
    '抽数数据源',      # 22
    '抽数主键'         # 23
]


def infer_db_type(database_name):
    """
    根据数据库名推断数据源类型

    Args:
        database_name: 数据库名

    Returns:
        数据源类型（mysql/tidb/adb）
    """
    return DB_NAME_TO_TYPE.get(database_name, 'mysql')


def infer_instance(database_name):
    """
    根据数据库名推断实例名

    Args:
        database_name: 数据库名

    Returns:
        实例名
    """
    return DATABASE_TO_INSTANCE_MAP.get(database_name, database_name)


def generate_datasource_name(db_type, instance, database):
    """
    生成抽数数据源名称

    格式：input_{数据源类型}_{实例}_{库}

    Args:
        db_type: 数据源类型
        instance: 实例名
        database: 数据库名

    Returns:
        数据源名称
    """
    return f"input_{db_type}_{instance}_{database}".lower()


if __name__ == '__main__':
    # 测试配置
    print("输出路径:", get_output_path())
    print("文件名:", generate_filename('success', 'test_table'))
    print("数据源类型:", infer_db_type('stjtestadb'))
    print("实例名:", infer_instance('stjtestadb'))
    print("数据源名:", generate_datasource_name('adb', 'sitadbrealtimedw', 'stjtestadb'))
