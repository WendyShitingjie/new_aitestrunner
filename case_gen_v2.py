#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 测试用例生成器 V2
根据目标知识要素定义自动生成完整的 YAML 测试用例

用法:
    python case_gen_v2.py <目标知识要素文件路径> [--run]

示例:
    # 仅生成用例
    python case_gen_v2.py TDD/REQ-33163-智能剧本推荐/elements/AI_copilot_ai_script_generate.yaml

    # 生成用例并执行
    python case_gen_v2.py TDD/REQ-33163-智能剧本推荐/elements/AI_copilot_ai_script_generate.yaml --run
"""

import sys
import argparse
import re
import yaml
from pathlib import Path
from openai import OpenAI
from config.settings import settings
from datetime import datetime
import subprocess
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class CaseGeneratorV2:
    """测试用例生成器 V2"""

    def __init__(self, target_element_path: str, auto_run: bool = False):
        """
        初始化生成器

        Args:
            target_element_path: 目标知识要素文件路径 (例如: TDD/REQ-33163-智能剧本推荐/elements/AI_copilot_ai_script_generate.yaml)
            auto_run: 是否自动执行测试
        """
        self.target_element_path = Path(target_element_path)
        self.project_root = Path(__file__).parent
        self.auto_run = auto_run

        # 校验文件是否存在
        if not self.target_element_path.exists():
            raise FileNotFoundError(f"目标知识要素文件不存在: {target_element_path}")

        # 解析目录结构: TDD/REQ-33163-智能剧本推荐/elements/AI_copilot_ai_script_generate.yaml
        # 获取需求目录 (TDD/REQ-33163-智能剧本推荐)
        self.req_dir = self.target_element_path.parent.parent
        print(f"📂 需求目录: {self.req_dir}")

        # 创建批次时间戳
        self.batch_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 初始化 cases 目录: TDD/REQ-33163-智能剧本推荐/cases
        self.cases_root_dir = self.req_dir / "cases"
        self.cases_root_dir.mkdir(parents=True, exist_ok=True)

        # 创建本次生成批次目录: TDD/REQ-33163-智能剧本推荐/cases/case_{timestamp}
        self.case_batch_dir = self.cases_root_dir / f"case_{self.batch_timestamp}"
        self.case_batch_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 用例批次目录: {self.case_batch_dir}")

        # 加载 LLM 配置
        # llm_config = settings.get('llm')
        # self.api_key = llm_config.get('api_key')
        # self.base_url = llm_config.get('base_url')
        # self.model = llm_config.get('model')
        self.api_key = os.getenv('LLM_API_KEY')
        self.base_url = os.getenv('LLM_BASE_URL')
        self.model = os.getenv('LLM_MODEL')
        print(f"🤖 LLM 模型: {self.model}")

        # 初始化 OpenAI 客户端
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def read_file(self, file_path: Path) -> str:
        """读取文件内容"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def load_target_element(self) -> dict:
        """
        加载目标知识要素定义

        Returns:
            dict: 目标知识要素的 YAML 内容
        """
        print(f"\n📖 正在读取目标知识要素: {self.target_element_path.name}")
        content = self.read_file(self.target_element_path)
        element = yaml.safe_load(content)

        element_code = element.get('code', 'Unknown')
        element_name = element.get('name', 'Unknown')
        print(f"   知识要素编号: {element_code}")
        print(f"   知识要素名称: {element_name}")

        return {
            'code': element_code,
            'name': element_name,
            'content': content,
            'data': element
        }

    def load_dependent_elements(self, target_element: dict) -> list:
        """
        加载依赖知识要素定义

        Args:
            target_element: 目标知识要素信息

        Returns:
            list: 依赖知识要素列表
        """
        dependencies = target_element['data'].get('dependencies', [])

        if not dependencies:
            print("\n⚠️  目标知识要素没有声明依赖知识要素")
            return []

        print(f"\n📚 正在加载 {len(dependencies)} 个依赖知识要素:")

        dependent_elements = []
        elements_dir = self.target_element_path.parent

        for dep in dependencies:
            dep_name = dep.get('code')
            if not dep_name:
                continue

            # 查找依赖知识要素文件
            dep_file = elements_dir / f"{dep_name}.yaml"

            if not dep_file.exists():
                print(f"   ⚠️  依赖知识要素文件不存在: {dep_file.name}")
                continue

            # 读取依赖知识要素内容
            dep_content = self.read_file(dep_file)
            dep_data = yaml.safe_load(dep_content)

            dep_element_code = dep_data.get('code', dep_name)
            dep_element_name = dep_data.get('name', 'Unknown')

            print(f"   ✓ {dep_element_code} - {dep_element_name}")

            dependent_elements.append({
                'code': dep_element_code,
                'name': dep_element_name,
                'content': dep_content,
                'data': dep_data
            })

        return dependent_elements

    def build_user_prompt(self, target_element: dict, dependent_elements: list) -> str:
        """
        构建用户提示词

        Args:
            target_element: 目标知识要素信息
            dependent_elements: 依赖知识要素列表

        Returns:
            str: 完整的用户提示词
        """
        print("\n🔧 正在构建用户提示词...")

        # 读取用户提示词模板
        user_prompt_template = self.read_file(
            self.project_root / "prompt" / "prompt.case_script_gen.user.md"
        )

        # 构造目标知识要素部分
        element_def_yaml = f"#### {target_element['code']} - {target_element['name']}\n"
        element_def_yaml += f"```yaml\n{target_element['content']}\n```\n"

        # 构造依赖知识要素部分
        dependent_elements_def_yaml = ""
        for dep in dependent_elements:
            dependent_elements_def_yaml += f"#### {dep['code']} - {dep['name']}\n"
            dependent_elements_def_yaml += f"```yaml\n{dep['content']}\n```\n\n"

        # 替换占位符
        user_prompt = user_prompt_template.replace("{element_def_yaml}", element_def_yaml)
        user_prompt = user_prompt.replace("{dependent_elements_def_yaml}", dependent_elements_def_yaml)

        print("   ✓ 用户提示词构建完成")

        # 保存用户提示词到批次目录
        user_prompt_file = self.case_batch_dir / "user_prompt.md"
        with open(user_prompt_file, "w", encoding="utf-8") as f:
            f.write(user_prompt)
        print(f"   ✓ 用户提示词已保存: {user_prompt_file}")

        return user_prompt

    def generate_test_cases(self, system_prompt: str, user_prompt: str) -> str:
        """
        调用 LLM 流式生成测试用例

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词

        Returns:
            str: 生成的完整 YAML 内容
        """
        print("\n🤖 正在调用 LLM 生成测试用例...")
        print("=" * 70)

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                stream=True,
            )

            full_response = ""

            # 流式输出
            for chunk in completion:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response += content

            print("\n" + "=" * 70)
            print("✓ LLM 响应完成")

            # 保存LLM原始响应
            llm_response_file = self.case_batch_dir / "llm_response.md"
            with open(llm_response_file, "w", encoding="utf-8") as f:
                f.write(full_response)
            print(f"✓ LLM 响应已保存: {llm_response_file}")

            return full_response

        except Exception as e:
            print(f"\n❌ LLM 调用失败: {e}")
            raise

    def extract_yaml_blocks(self, content: str) -> list:
        """
        从 LLM 响应中提取 YAML 代码块

        Args:
            content: LLM 响应内容

        Returns:
            list: YAML 字符串列表
        """
        # 匹配 ```yaml ... ``` 代码块
        pattern = r'```yaml\s*\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)

        if not matches:
            print("\n⚠️  未找到有效的 YAML 代码块，尝试直接解析...")
            # 如果没有代码块标记，尝试直接返回内容
            return [content]

        return matches

    def parse_and_save_test_cases(self, yaml_content: str) -> list:
        """
        解析并保存测试用例

        Args:
            yaml_content: YAML 格式的测试用例内容

        Returns:
            list: 保存的测试用例文件路径列表
        """
        print("\n📝 正在解析并保存测试用例...")

        # 提取 YAML 代码块
        yaml_blocks = self.extract_yaml_blocks(yaml_content)

        saved_files = []

        for block in yaml_blocks:
            try:
                # 尝试解析 YAML
                parsed = yaml.safe_load(block)

                if parsed is None:
                    continue

                # 如果是字典，转为列表
                if isinstance(parsed, dict):
                    test_cases = [parsed]
                elif isinstance(parsed, list):
                    test_cases = parsed
                else:
                    print(f"   ⚠️  无法识别的数据类型: {type(parsed)}")
                    continue

                # 保存每个测试用例
                for test_case in test_cases:
                    if not isinstance(test_case, dict):
                        continue

                    case_code = test_case.get('case_code')

                    if not case_code:
                        print("   ⚠️  测试用例缺少 case_code，跳过")
                        continue

                    # 构造文件名: case_code.yaml
                    file_name = f"{case_code}.yaml"
                    file_path = self.case_batch_dir / file_name

                    # 保存为 YAML 文件
                    with open(file_path, 'w', encoding='utf-8') as f:
                        yaml.dump(test_case, f,
                                allow_unicode=True,
                                default_flow_style=False,
                                sort_keys=False)

                    case_name = test_case.get('case_name', 'N/A')
                    print(f"   ✓ 已保存: {file_name} - {case_name}")
                    saved_files.append(file_path)

            except yaml.YAMLError as e:
                print(f"   ❌ YAML 解析失败: {e}")
                # 保存原始内容到文件用于调试
                error_file = self.case_batch_dir / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(error_file, 'w', encoding='utf-8') as f:
                    f.write(block)
                print(f"   原始内容已保存到: {error_file}")
            except Exception as e:
                print(f"   ❌ 处理失败: {e}")

        print(f"\n✓ 共保存 {len(saved_files)} 个测试用例文件")
        return saved_files

    def execute_test_cases(self):
        """执行生成的测试用例"""
        if not self.auto_run:
            print("\n⏭️  跳过测试执行（未指定 --run 参数）")
            return

        print("\n🚀 正在执行测试用例...")
        print("=" * 70)

        # 调用 case_run_v2.py 批量执行
        run_test_script = self.project_root / "case_run_v2.py"
        case_batch_dir_str = str(self.case_batch_dir)

        try:
            # 使用 subprocess 调用 case_run_v2.py
            result = subprocess.run(
                [sys.executable, str(run_test_script), case_batch_dir_str],
                cwd=str(self.project_root),
                capture_output=False,
                text=True
            )

            if result.returncode == 0:
                print("\n✓ 测试用例执行完成")
            else:
                print(f"\n⚠️  测试用例执行返回非零状态码: {result.returncode}")

        except Exception as e:
            print(f"\n❌ 测试用例执行失败: {e}")

    def run(self):
        """运行完整的生成流程"""
        print("=" * 70)
        print("  AI 测试用例自动生成器 V2")
        print("=" * 70)

        # 1. 加载目标知识要素
        target_element = self.load_target_element()

        # print(f'target_element: {target_element}')

        # 2. 加载依赖知识要素
        dependent_elements = self.load_dependent_elements(target_element)

        # 3. 构建用户提示词
        user_prompt = self.build_user_prompt(target_element, dependent_elements)

        # 4. 读取系统提示词
        print("\n📖 正在读取系统提示词...")
        system_prompt = self.read_file(
            self.project_root / "prompt" / "prompt.case_script_gen.system.md"
        )
        print("   ✓ 系统提示词加载完成")

        # 5. 调用 LLM 生成测试用例
        llm_response = self.generate_test_cases(system_prompt, user_prompt)

        # 6. 解析并保存测试用例
        saved_files = self.parse_and_save_test_cases(llm_response)

        if not saved_files:
            print("\n⚠️  没有生成有效的测试用例文件，跳过执行")
            return

        # 7. 执行测试用例（如果指定了 --run 参数）
        self.execute_test_cases()

        # 8. 输出总结
        print("\n" + "=" * 70)
        print("📊 生成完成")
        print("=" * 70)
        print(f"用例批次目录: {self.case_batch_dir}")
        print(f"生成用例数量: {len(saved_files)}")
        if self.auto_run:
            print(f"测试报告目录: {self.req_dir / 'reports' / self.case_batch_dir.name}")
        print("=" * 70)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='AI 测试用例自动生成器 V2 - 根据目标知识要素定义自动生成测试用例',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 仅生成用例
  python case_gen_v2.py TDD/REQ-33163-智能剧本推荐/elements/AI_copilot_ai_script_generate.yaml

  # 生成用例并执行
  python case_gen_v2.py TDD/REQ-33163-智能剧本推荐/elements/AI_copilot_ai_script_generate.yaml --run
        """
    )

    parser.add_argument(
        'element_path',
        type=str,
        help='目标知识要素文件路径（例如: TDD/REQ-33163-智能剧本推荐/elements/AI_copilot_ai_script_generate.yaml）'
    )

    parser.add_argument(
        '--run',
        action='store_true',
        help='生成用例后自动执行测试'
    )

    args = parser.parse_args()

    try:
        # 创建生成器实例
        generator = CaseGeneratorV2(args.element_path, auto_run=args.run)

        # 运行生成流程
        generator.run()

        print("\n✅ 所有任务完成!")

    except FileNotFoundError as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
