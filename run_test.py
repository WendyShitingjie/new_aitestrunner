#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行测试用例（支持单个或批量执行）

用法:
    # 单个测试用例
    python run_test.py <测试用例路径>

    # 批量执行（目录下所有.yaml文件）
    python run_test.py <测试用例目录>

示例:
    # 单个用例
    python run_test.py cases/TC_TKF001_001_离线剧本批量生成_正常流程.yaml

    # 批量执行
    python run_test.py cases
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import os

# --- 修改这部分 ---
# 现在 run_test.py 在项目根目录下
current_dir = Path(__file__).parent
project_root = current_dir  # 当前目录就是项目根目录

# 将真正的项目根目录加入 sys.path
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入核心模块
from core.executor import AITestExecutor
from actions.action_registry import action_registry

# 为了向后兼容，重命名函数
def register_all_actions():
    """注册所有动作的兼容函数"""
    action_registry.discover()

# ------------------


def execute_single_test(executor, test_case_path, task_dir=None):
    """
    执行单个测试用例

    Args:
        executor: 测试执行器
        test_case_path: 测试用例文件路径
        task_dir: 任务目录（批量执行时使用）

    Returns:
        dict: 测试结果信息
    """
    print(f"\nStarting execution of test case: {test_case_path.name}")

    # 读取YAML文件内容
    with open(test_case_path, 'r', encoding='utf-8') as f:
        test_case_yaml = f.read()

    # 如果是批量执行，修改报告输出目录
    if task_dir:
        executor.html_reporter.output_dir = str(task_dir)

    # 执行测试用例
    result = executor.execute_test_case(test_case_yaml)

    # 打印结果
    print("\n" + "="*60)
    print(f"Test Result: {result.status}")
    print(f"Execution time: {result.execution_time:.2f} seconds")
    print("="*60)

    # 获取报告路径
    report_path = None
    if executor.html_reporter:
        # 报告已经在execute_test_case中生成
        # 获取最新生成的报告路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_case_id = result.test_case_id
        report_filename = f"{test_case_id}_{timestamp}.html"
        if task_dir:
            report_path = task_dir / report_filename
        else:
            report_path = Path(executor.html_reporter.output_dir) / report_filename

    return {
        'test_case_id': result.test_case_id,
        'test_name': result.test_name,
        'status': result.status,
        'execution_time': result.execution_time,
        'assertions': executor.execution_details.get('assertions', []),
        'report_path': report_path,
        'test_case_file': test_case_path.name
    }


def create_index_html(task_dir, results):
    """
    创建汇总报告 index.html

    Args:
        task_dir: 任务目录
        results: 测试结果列表
    """
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['status'] == 'PASS')
    failed_tests = total_tests - passed_tests
    total_time = sum(r['execution_time'] for r in results)

    # 计算通过率
    pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试报告汇总 - {task_dir.name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB',
                         'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
            font-weight: 600;
        }}

        .header .subtitle {{
            font-size: 16px;
            opacity: 0.9;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px 40px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }}

        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            text-align: center;
        }}

        .summary-card .label {{
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 8px;
        }}

        .summary-card .value {{
            font-size: 32px;
            font-weight: 700;
            color: #212529;
        }}

        .summary-card.pass .value {{
            color: #28a745;
        }}

        .summary-card.fail .value {{
            color: #dc3545;
        }}

        .summary-card.rate .value {{
            color: #667eea;
        }}

        .test-list {{
            padding: 40px;
        }}

        .test-list h2 {{
            font-size: 24px;
            margin-bottom: 20px;
            color: #212529;
        }}

        .test-item {{
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
        }}

        .test-item:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }}

        .test-item-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}

        .test-item-title {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .status-badge.pass {{
            background: #d4edda;
            color: #155724;
        }}

        .status-badge.fail {{
            background: #f8d7da;
            color: #721c24;
        }}

        .test-id {{
            font-size: 18px;
            font-weight: 600;
            color: #212529;
        }}

        .test-name {{
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 10px;
        }}

        .test-meta {{
            display: flex;
            gap: 20px;
            font-size: 13px;
            color: #6c757d;
        }}

        .test-meta-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        .test-actions {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e9ecef;
        }}

        .btn {{
            display: inline-block;
            padding: 8px 16px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-size: 14px;
            transition: all 0.3s ease;
        }}

        .btn:hover {{
            background: #5568d3;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            color: #6c757d;
            font-size: 14px;
        }}

        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745 0%, #20c997 100%);
            transition: width 0.3s ease;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 测试报告汇总</h1>
            <div class="subtitle">任务: {task_dir.name}</div>
        </div>

        <div class="summary">
            <div class="summary-card">
                <div class="label">总用例数</div>
                <div class="value">{total_tests}</div>
            </div>
            <div class="summary-card pass">
                <div class="label">通过</div>
                <div class="value">{passed_tests}</div>
            </div>
            <div class="summary-card fail">
                <div class="label">失败</div>
                <div class="value">{failed_tests}</div>
            </div>
            <div class="summary-card rate">
                <div class="label">通过率</div>
                <div class="value">{pass_rate:.1f}%</div>
            </div>
            <div class="summary-card">
                <div class="label">总耗时</div>
                <div class="value">{total_time:.1f}s</div>
            </div>
        </div>

        <div class="test-list">
            <h2>📋 测试用例列表</h2>
"""

    # 添加每个测试用例
    for i, result in enumerate(results, 1):
        status_class = 'pass' if result['status'] == 'PASS' else 'fail'
        status_text = '✅ PASS' if result['status'] == 'PASS' else '❌ FAIL'

        # 计算断言统计
        assertions = result.get('assertions', [])
        total_assertions = len(assertions)
        passed_assertions = sum(1 for a in assertions if a.get('status') == 'PASS')

        # 报告链接
        report_link = result['report_path'].name if result['report_path'] else '#'

        html_content += f"""
            <div class="test-item">
                <div class="test-item-header">
                    <div class="test-item-title">
                        <span class="status-badge {status_class}">{status_text}</span>
                        <span class="test-id">{result['test_case_id']}</span>
                    </div>
                </div>
                <div class="test-name">{result['test_name']}</div>
                <div class="test-meta">
                    <div class="test-meta-item">
                        <span>⏱️</span>
                        <span>{result['execution_time']:.2f}秒</span>
                    </div>
                    <div class="test-meta-item">
                        <span>📝</span>
                        <span>{total_assertions} 个断言</span>
                    </div>
                    <div class="test-meta-item">
                        <span>✅</span>
                        <span>{passed_assertions} 通过</span>
                    </div>
                    <div class="test-meta-item">
                        <span>📄</span>
                        <span>{result['test_case_file']}</span>
                    </div>
                </div>
                <div class="test-actions">
                    <a href="{report_link}" class="btn" target="_blank">查看详细报告</a>
                </div>
            </div>
"""

    html_content += f"""
        </div>

        <div class="footer">
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>AI测试框架 v1.0</p>
        </div>
    </div>
</body>
</html>
"""

    # 写入文件
    index_path = task_dir / 'index.html'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return index_path


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='运行AI测试框架的测试用例（支持单个或批量执行）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 单个用例
  python run_test.py cases/TC_TKF001_001_离线剧本批量生成_正常流程.yaml

  # 批量执行
  python run_test.py cases
        """
    )
    parser.add_argument(
        'path',
        type=str,
        help='测试用例文件路径或目录（相对于run_test.py所在目录）'
    )

    args = parser.parse_args()

    # 注册所有动作
    register_all_actions()

    # 获取路径
    input_path = project_root / args.path

    # 检查路径是否存在
    if not input_path.exists():
        print(f"\nError: 路径不存在: {args.path}")
        print(f"   完整路径: {input_path}")
        sys.exit(1)

    # 判断是文件还是目录
    if input_path.is_file():
        # 单个测试用例
        print("="*70)
        print("  AI Test Framework - Single Test Case Execution")
        print("="*70)

        # 初始化执行器
        print("\nInitializing test executor...")
        executor = AITestExecutor()

        # 执行测试
        result = execute_single_test(executor, input_path)

        # 打印详细结果
        print("\n" + "="*70)
        print("📊 测试结果汇总")
        print("="*70)
        print(f"测试用例ID: {result['test_case_id']}")
        print(f"测试名称: {result['test_name']}")
        print(f"执行状态: {result['status']}")
        print(f"执行时间: {result['execution_time']:.2f}秒")

        # 断言详情
        all_assertions = result['assertions']
        print(f"断言数量: {len(all_assertions)}")

        if all_assertions:
            print("\n断言详情:")
            for assertion in all_assertions:
                status_icon = "✅" if assertion.get('status') == 'PASS' else "❌"
                intent = assertion.get('intent', 'N/A')
                action = assertion.get('action', 'N/A')
                print(f"  {status_icon} {intent}")
                if assertion.get('status') == 'FAIL':
                    print(f"      动作: {action}")
                    print(f"      错误: {assertion.get('error', 'N/A')}")

        print("="*70)

    elif input_path.is_dir():
        # 批量执行
        print("="*70)
        print("  AI Test Framework - Batch Execution")
        print("="*70)

        # 查找所有.yaml文件
        yaml_files = sorted(input_path.glob('*.yaml'))

        if not yaml_files:
            print(f"\nWarning: 目录中没有找到.yaml文件: {args.path}")
            sys.exit(0)

        print(f"Found {len(yaml_files)} test case files")

        # 创建任务目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_dir = project_root / 'reports' / f'task_{timestamp}'
        task_dir.mkdir(parents=True, exist_ok=True)

        print(f"Output Directory: {task_dir}")

        # 初始化执行器
        print("\nInitializing test executor...")
        executor = AITestExecutor()

        # 执行所有测试用例
        results = []
        print("\n" + "="*70)
        print("Start executing test cases...")
        print("="*70)

        for i, yaml_file in enumerate(yaml_files, 1):
            print(f"\n[{i}/{len(yaml_files)}] " + "="*60)
            try:
                result = execute_single_test(executor, yaml_file, task_dir)
                results.append(result)
            except Exception as e:
                print(f"Execution failed: {e}")
                # 记录失败的用例
                results.append({
                    'test_case_id': yaml_file.stem,
                    'test_name': yaml_file.name,
                    'status': 'FAIL',
                    'execution_time': 0,
                    'assertions': [],
                    'report_path': None,
                    'test_case_file': yaml_file.name
                })

        # 生成汇总报告
        print("\n" + "="*70)
        print("Generate Summary Report...")
        print("="*70)

        index_path = create_index_html(task_dir, results)

        # 打印汇总统计
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r['status'] == 'PASS')
        failed_tests = total_tests - passed_tests
        total_time = sum(r['execution_time'] for r in results)
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        print("\n" + "="*70)
        print("Batch Execution Summary")
        print("="*70)
        print(f"Total Cases: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        print(f"Total Time: {total_time:.2f} seconds")
        print(f"\nSummary Report: {index_path}")
        print("="*70)

        # 列出失败的用例
        if failed_tests > 0:
            print("\nFailed test cases:")
            for result in results:
                if result['status'] == 'FAIL':
                    print(f"  - {result['test_case_id']}: {result['test_name']}")

    else:
        print(f"\nError: 路径既不是文件也不是目录: {args.path}")
        sys.exit(1)


if __name__ == '__main__':
    main()

