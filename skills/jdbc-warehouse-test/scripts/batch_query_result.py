#!/usr/bin/env python3
"""
查询批量操作校验结果接口脚本
调用 /dataops/etlx/batch/v2/task/{taskId}/result 接口
支持轮询等待异步校验完成
"""
import requests
import sys
import json
import time

# 导入 API 配置
from api_config import get_api_url


def query_validate_result(task_id, env=None):
    """
    查询批量操作校验结果

    Args:
        task_id: 任务ID
        env: 环境名称（sit03/sit01/prod），默认 sit03

    Returns:
        dict: 接口响应结果
    """
    # 从配置文件获取接口地址
    url = get_api_url('batch_validate_result', env=env, taskId=task_id)

    print("=" * 60)
    print("查询批量操作校验结果")
    print("=" * 60)
    print(f"接口地址: {url}")
    print(f"任务ID: {task_id}")
    print("=" * 60)
    print()

    try:
        # 发送 GET 请求
        print("正在查询校验结果...")
        response = requests.get(url, timeout=30)

        # 打印响应
        print(f"HTTP 状态码: {response.status_code}")
        print()

        # 解��响应
        result = response.json()

        print("=" * 60)
        print("接口响应")
        print("=" * 60)
        print(f"code: {result.get('code')}")
        print(f"success: {result.get('success')}")
        print(f"failure: {result.get('failure')}")
        print(f"message: {result.get('message')}")

        if result.get('data'):
            print()
            print("校验结果数据:")
            data = result['data']

            # 失败统计
            publish_failed_count = data.get('publishFailedCount', 0)
            print(f"  publishFailedCount: {publish_failed_count}")

            # 失败行详情
            failed_rows = data.get('failedRows', [])
            if failed_rows:
                print(f"  failedRows: {len(failed_rows)} 行失败")
                print()
                print("  失败行详情:")
                for idx, row in enumerate(failed_rows[:5], 1):  # 最多显示前5行
                    print(f"    [{idx}] 行号: {row.get('rowIndex')}, 原因: {row.get('reason')}")
                if len(failed_rows) > 5:
                    print(f"    ... 还有 {len(failed_rows) - 5} 行失败")
            else:
                print(f"  failedRows: 无失败行")

            # 解析失败行
            parse_failed_rows = data.get('parseFailedRows', [])
            if parse_failed_rows:
                print(f"  parseFailedRows: {len(parse_failed_rows)} 行解析失败")

            # 失败原因统计
            failure_statistics = data.get('failureStatistics', {})
            if failure_statistics:
                print()
                print("  失败原因统计:")
                for reason, count in failure_statistics.items():
                    print(f"    {reason}: {count}")

        print("=" * 60)
        print()

        # 判断校验结果
        if result.get('code') == 0 and result.get('success'):
            publish_failed_count = result.get('data', {}).get('publishFailedCount', 0)
            failed_rows = result.get('data', {}).get('failedRows', [])

            if publish_failed_count == 0 and len(failed_rows) == 0:
                print("✅ 校验成功！所有任务通过校验")
                print()
                print("后续操作:")
                print(f"1. 提交任务: POST /dataops/etlx/batch/v2/submit/{task_id}")
                print(f"2. 模拟 BPM 审批通过: 使用 mq-sender 发送审批通过消息")
            else:
                print("❌ 校验失败！存在未通过校验的任务")
                print()
                print(f"失败任务数: {publish_failed_count}")
                print(f"失败行数: {len(failed_rows)}")
                print()
                print("建议:")
                print("- 检查失败原因")
                print("- 修复问题后重新上传")
        else:
            print("❌ 查询失败！")
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


def wait_for_validation_complete(task_id, env=None, max_retries=10, interval=5):
    """
    轮询等待批量操作校验完成

    Args:
        task_id: 任务ID
        env: 环境名称（sit03/sit01/prod），默认 sit03
        max_retries: 最大重试次数，默认 10 次
        interval: 每次重试的间隔时间（秒），默认 5 秒

    Returns:
        dict: 接口响应结果，如果超时返回 None
    """
    print("=" * 60)
    print("⏳ 等待异步校验完成...")
    print("=" * 60)
    print(f"任务ID: {task_id}")
    print(f"最大重试次数: {max_retries}")
    print(f"重试间隔: {interval} 秒")
    print(f"最大等待时间: {max_retries * interval} 秒")
    print("=" * 60)
    print()

    for attempt in range(1, max_retries + 1):
        print(f"[第 {attempt}/{max_retries} 次查询] 正在查询校验结果...")

        # 调用查询接口（静默模式）
        url = get_api_url('batch_validate_result', env=env, taskId=task_id)

        try:
            response = requests.get(url, timeout=30)
            result = response.json()

            # 检查是否校验完成
            if result.get('code') == 0 and result.get('data'):
                data = result['data']
                publish_failed_count = data.get('publishFailedCount')

                # 如果 publishFailedCount 有值（不为 None），说明校验完成
                if publish_failed_count is not None:
                    print(f"✅ 校验已完成！（第 {attempt} 次查询）")
                    print()

                    # 显示校验结果
                    failed_rows = data.get('failedRows', [])
                    if publish_failed_count == 0 and len(failed_rows) == 0:
                        print("✅ 校验成功！所有任务通过校验")
                    else:
                        print(f"⚠️ 校验失败！失败任务数: {publish_failed_count}, 失败行数: {len(failed_rows)}")

                    print()
                    return result

            # 校验未完成，继续等待
            if attempt < max_retries:
                print(f"   校验尚未完成，{interval} 秒后重试...\n")
                time.sleep(interval)

        except Exception as e:
            print(f"   查询出错: {str(e)}")
            if attempt < max_retries:
                print(f"   {interval} 秒后重试...\n")
                time.sleep(interval)

    # 超时
    print("❌ 等待超时！校验未在预期时间内完成")
    print(f"建议: 手动执行 python batch_query_result.py {task_id} 查看详情")
    return None


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python batch_query_result.py <task_id> [env] [--wait]")
        print()
        print("参数:")
        print("  task_id - 任务ID（必需）")
        print("  env     - 环境名称（可选，默认 sit03）")
        print("            可选值: sit03, sit01, prod")
        print("  --wait  - 轮询等待校验完成（可选）")
        print()
        print("示例:")
        print("  python batch_query_result.py 404")
        print("  python batch_query_result.py 404 sit03")
        print("  python batch_query_result.py 404 sit03 --wait")
        print("  python batch_query_result.py 404 --wait")
        sys.exit(1)

    task_id = sys.argv[1]
    env = None
    wait_mode = False

    # 解析参数
    for arg in sys.argv[2:]:
        if arg == '--wait':
            wait_mode = True
        elif arg in ['sit03', 'sit01', 'prod']:
            env = arg

    # 根据模式选择执行方式
    if wait_mode:
        result = wait_for_validation_complete(task_id, env)
    else:
        result = query_validate_result(task_id, env)

    # 判断是否成功
    if result and result.get('code') == 0:
        publish_failed_count = result.get('data', {}).get('publishFailedCount', 0)
        if publish_failed_count == 0:
            sys.exit(0)  # 校验通过
        else:
            sys.exit(2)  # 校验失败
    else:
        sys.exit(1)  # 接口调用失败
