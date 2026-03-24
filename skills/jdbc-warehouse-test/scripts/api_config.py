#!/usr/bin/env python3
"""
API 域名配置文件
管理各个服务的域名配置
"""

# ============= 环境配置 =============
# 默认环境
DEFAULT_ENV = 'sit03'

# 环境域名模板
ENV_DOMAIN_TEMPLATES = {
    'sit03': 'http://{application}.apps01.ali-bj-sit03.shuheo.net',
    'sit01': 'http://{application}.apps01.ali-bj-sit01.shuheo.net',
    'prod': 'http://{application}.dmz.prod.caijj.net',
}

# ============= 服务域名配置 =============
# 各服���的域名配置（如果有特殊映射，在这里定义）
SERVICE_DOMAINS = {
    'sit03': {
        'firekylin': 'http://firekylin.apps01.ali-bj-sit03.shuheo.net',
        'dataops': 'http://dataops.apps01.ali-bj-sit03.shuheo.net',
        'datagovernor': 'http://datagovernor.apps01.ali-bj-sit03.shuheo.net',
        'featurestore': 'http://featurestore.apps01.ali-bj-sit03.shuheo.net',
    },
    'sit01': {
        'firekylin': 'http://firekylin.apps01.ali-bj-sit01.shuheo.net',
        'dataops': 'http://dataops.apps01.ali-bj-sit01.shuheo.net',
    },
    'prod': {
        'dataops': 'http://dataops.dmz.prod.caijj.net',
    }
}

# ============= 接口路径配置 =============
# 各接口的路径（从 TKI 文档中提取）
API_PATHS = {
    # 批量入仓相关接口
    'batch_validate': '/dataops/etlx/batch/v2/validate',  # TKI_003: 批量上传校验
    'batch_validate_result': '/dataops/etlx/batch/v2/task/{taskId}/result',  # TKI_004: 查询校验结果
    'batch_submit': '/dataops/etlx/batch/v2/submit/{taskId}',  # TKI_005: 提交任务
    'batch_cancel': '/dataops/etlx/batch/v2/task/cancel',  # TKI_006: 取消任务

    # 元数据管理接口
    'metadata_get': '/firekylin/mysql-metadata/mysql/table/metadata',  # 查询元数据
    'metadata_manage': '/firekylin/mysql-metadata/mysql/table/metadata:manage',  # 管理元数据
}


def get_service_domain(application, env=None):
    """
    获取服务域名

    Args:
        application: 应用名称（如：dataops, firekylin）
        env: 环境名称（如：sit03, sit01, prod），默认使用 DEFAULT_ENV

    Returns:
        str: 完整的服务域名
    """
    if env is None:
        env = DEFAULT_ENV

    # 优先从 SERVICE_DOMAINS 中查找
    if env in SERVICE_DOMAINS and application in SERVICE_DOMAINS[env]:
        return SERVICE_DOMAINS[env][application]

    # 否则使用模板拼接
    if env in ENV_DOMAIN_TEMPLATES:
        template = ENV_DOMAIN_TEMPLATES[env]
        return template.format(application=application)

    # 默认使用 sit03 模板
    template = ENV_DOMAIN_TEMPLATES[DEFAULT_ENV]
    return template.format(application=application)


def get_api_url(api_key, application=None, env=None, **path_params):
    """
    获取完整的 API URL

    Args:
        api_key: API 路径的键（如：batch_validate）
        application: 应用名称，如果不提供则从 API_PATHS 中推断
        env: 环境名称
        **path_params: 路径参数（如：taskId=123）

    Returns:
        str: 完整的 API URL
    """
    # 获取 API 路径
    if api_key not in API_PATHS:
        raise ValueError(f"未知的 API 键: {api_key}")

    api_path = API_PATHS[api_key]

    # 格式化路径参数
    if path_params:
        api_path = api_path.format(**path_params)

    # 推断 application（从路径中提取第一个段）
    if application is None:
        path_parts = api_path.split('/')
        if len(path_parts) > 1:
            application = path_parts[1]

    # 获取服务域名
    domain = get_service_domain(application, env)

    # 拼接完整 URL
    return f"{domain}{api_path}"


def get_api_info(api_key):
    """
    获取 API 信息

    Args:
        api_key: API 路径的键

    Returns:
        dict: API 信息
    """
    if api_key not in API_PATHS:
        raise ValueError(f"未知的 API 键: {api_key}")

    api_path = API_PATHS[api_key]

    # 从路径推断 application
    path_parts = api_path.split('/')
    application = path_parts[1] if len(path_parts) > 1 else None

    return {
        'api_key': api_key,
        'path': api_path,
        'application': application,
    }


# ============= 测试函数 =============
def test_config():
    """测试配置"""
    print("=" * 60)
    print("API 域名配置测试")
    print("=" * 60)

    # 测试获取服务域名
    print("\n1. 获取服务域名:")
    print(f"   dataops (sit03): {get_service_domain('dataops', 'sit03')}")
    print(f"   firekylin (sit03): {get_service_domain('firekylin', 'sit03')}")
    print(f"   dataops (sit01): {get_service_domain('dataops', 'sit01')}")

    # 测试获取 API URL
    print("\n2. 获取 API URL:")
    print(f"   batch_validate: {get_api_url('batch_validate')}")
    print(f"   batch_validate_result: {get_api_url('batch_validate_result', taskId=123)}")
    print(f"   metadata_get: {get_api_url('metadata_get')}")

    # 测试获取 API 信息
    print("\n3. 获取 API 信息:")
    for api_key in ['batch_validate', 'metadata_get']:
        info = get_api_info(api_key)
        print(f"   {api_key}:")
        print(f"     application: {info['application']}")
        print(f"     path: {info['path']}")

    print("=" * 60)


if __name__ == '__main__':
    test_config()
