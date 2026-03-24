#!/usr/bin/env python3
"""
批量上传校验接口测试脚本
调用 /dataops/etlx/batch/v2/validate 接口
"""
import requests
import os
import sys

# 导入 API 配置
from api_config import get_api_url


def upload_validate(file_path, env=None, task_id=None):
    """
    调用批量上传校验接口

    Args:
        file_path: Excel 文件路径
        env: 环境名称（sit03/sit01/prod），默认 sit03
        task_id: 任务ID（可选，修改任务时传入）

    Returns:
        dict: 接口响应结果
    """
    # 从配置文件获取接口地址
    url = get_api_url('batch_validate', env=env)

    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 构造请求参数
    params = {
        'optionType': 'UPLOAD',
        'p_n': '施婷杰',
        'p_u': '71e8b23d-45e2-497a-b247-f5b807fb4f65'
    }

    # 如果有 taskId，添加到参数中
    if task_id:
        params['taskId'] = task_id

    # 构造 HTTP Header（中文需要进行 URL 编码）
    import urllib.parse
    headers = {
        'p_n': urllib.parse.quote('施婷杰'),
        'p_u': '71e8b23d-45e2-497a-b247-f5b807fb4f65'
    }

    # 准备文件
    file_name = os.path.basename(file_path)

    print("=" * 60)
    print("批量上传校验接口测试")
    print("=" * 60)
    print(f"接口地址: {url}")
    print(f"文件路径: {file_path}")
    print(f"文件名称: {file_name}")
    print(f"操作类型: UPLOAD")
    print(f"创建人: 施婷杰")
    print(f"创建人UID: 71e8b23d-45e2-497a-b247-f5b807fb4f65")
    if task_id:
        print(f"任务ID: {task_id}")
    print("=" * 60)
    print()

    try:
        # 打开文件并发送请求
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_name, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            }

            print("正在上传文件...")
            response = requests.post(
                url,
                params=params,
                files=files,
                headers=headers,
                timeout=60
            )

        # 打印响应
        print(f"HTTP 状态码: {response.status_code}")
        print()

        # 解析响应
        result = response.json()

        print("=" * 60)
        print("接口响应")
        print("=" * 60)
        print(f"code: {result.get('code')}")
        print(f"success: {result.get('success')}")
        print(f"message: {result.get('message')}")

        if result.get('data'):
            print()
            print("返回数据:")
            data = result['data']
            for key, value in data.items():
                print(f"  {key}: {value}")

        print("=" * 60)
        print()

        # 判断是否成功
        if result.get('code') == 0 and result.get('success'):
            print("✅ 校验成功！")
            if result.get('data', {}).get('taskId'):
                task_id = result['data']['taskId']
                print(f"\n📝 任务ID: {task_id}")

                # 获取查询结果接口 URL
                result_url = get_api_url('batch_validate_result', env=env, taskId=task_id)
                print(f"\n后续操作:")
                print(f"1. 查询校验结果:")
                print(f"   GET {result_url}")
                print(f"2. 模拟 BPM 审批通过:")
                print(f"   使用 mq-sender 发送审批通过消息")
        else:
            print("❌ 校验失败！")
            print(f"错误信息: {result.get('message')}")

        return result

    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python batch_upload_validate.py <file_path> [env] [task_id]")
        print()
        print("参数:")
        print("  file_path - Excel 文件路径（必需）")
        print("  env       - 环境名称（可选，默认 sit03）")
        print("              可选值: sit03, sit01, prod")
        print("  task_id   - 任务ID（可选，修改任务时使用）")
        print()
        print("示例:")
        print("  python batch_upload_validate.py test.xlsx")
        print("  python batch_upload_validate.py test.xlsx sit03")
        print("  python batch_upload_validate.py test.xlsx sit03 123")
        sys.exit(1)

    file_path = sys.argv[1]
    env = sys.argv[2] if len(sys.argv) > 2 else None
    task_id = sys.argv[3] if len(sys.argv) > 3 else None

    result = upload_validate(file_path, env, task_id)

    if result and result.get('code') == 0:
        sys.exit(0)
    else:
        sys.exit(1)
