#!/usr/bin/env python3
"""
提交批量操作任务接口脚本
调用 /dataops/etlx/batch/v2/submit/{taskId} 接口
"""
import requests
import sys

# 导入 API 配置
from api_config import get_api_url


def submit_task(task_id, env=None):
    """
    提交批量操作任务

    Args:
        task_id: 任务ID
        env: 环境名称（sit03/sit01/prod），默认 sit03

    Returns:
        dict: 接口响应结果
    """
    # 从配置文件获取接口地址
    url = get_api_url('batch_submit', env=env, taskId=task_id)

    # 构造 HTTP Header（中文需要进行 URL 编码）
    import urllib.parse
    headers = {
        'p_n': urllib.parse.quote('施婷杰'),
        'p_u': '71e8b23d-45e2-497a-b247-f5b807fb4f65'
    }

    # 构造 Query Parameter
    params = {
        'p_n': '施婷杰',
        'p_u': '71e8b23d-45e2-497a-b247-f5b807fb4f65'
    }

    print("=" * 60)
    print("提交批量操作任务")
    print("=" * 60)
    print(f"接口地址: {url}")
    print(f"任务ID: {task_id}")
    print(f"创建人: 施婷杰")
    print(f"创建人UID: 71e8b23d-45e2-497a-b247-f5b807fb4f65")
    print("=" * 60)
    print()

    try:
        # 发送 POST 请求
        print("正在提交任务...")
        response = requests.post(url, headers=headers, params=params, timeout=30)

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
        print(f"data: {result.get('data')}")
        print("=" * 60)
        print()

        # 判断是否成功
        if result.get('code') == 0 and result.get('success'):
            print("✅ 提交成功！")
            print()
            print("任务状态已更新为: PENDING_APPROVAL (待审批)")
            print("BPM 工单已生成")
            print()
            print("后续操作:")
            print(f"1. 使用 mq-sender 发送审批通过消息:")
            print(f"   /mq-sender 发送批量入仓-新增任务(taskId={task_id})的审批通过的bpm消息")
            print(f"2. 或使用自然语言:")
            print(f"   帮我把 taskId={task_id} 的任务发送审批通过消息")
        else:
            print("❌ 提交失败！")
            print(f"错误信息: {result.get('message')}")
            print()
            print("可能原因:")
            print("- 任务未通过校验（task_status != 'VALIDATE_SUCCESS'）")
            print("- 任务ID不存在")
            print("- 任务已经提交过")

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
        print("用法: python batch_submit_task.py <task_id> [env]")
        print()
        print("参数:")
        print("  task_id - 任务ID（必需）")
        print("  env     - 环境名称（可选，默认 sit03）")
        print("            可选值: sit03, sit01, prod")
        print()
        print("示例:")
        print("  python batch_submit_task.py 404")
        print("  python batch_submit_task.py 404 sit03")
        sys.exit(1)

    task_id = sys.argv[1]
    env = sys.argv[2] if len(sys.argv) > 2 else None

    result = submit_task(task_id, env)

    if result and result.get('code') == 0:
        sys.exit(0)
    else:
        sys.exit(1)
