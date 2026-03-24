"""Skill 桥接动作 - 调用 Skill 执行任务"""
import subprocess
import sys
import os
from typing import Any, Dict
from pathlib import Path

from actions.action_registry import action_registry
from actions.base import ExecutionAction, ActionMetadata
from actions.skill_discoverer import SkillDiscoverer


@action_registry.register_decorator()
class BridgeSkillAction(ExecutionAction):
    """Skill 桥接动作 - 用于调用 Skill 执行特定任务"""

    metadata = ActionMetadata(
        name='bridge_skill',
        category='skill',
        description='桥接 Skill 工具执行任务，支持生成测试文件、数据准备等操作',
        parameters=[
            {
                'name': 'skill_name',
                'type': 'str',
                'required': True,
                'description': 'Skill 名称，如 jdbc-warehouse-test, mq-sender, test-table'
            },
            {
                'name': 'action',
                'type': 'str',
                'required': True,
                'description': 'Skill 动作名称，如 generate_excel, send_mq'
            },
            {
                'name': 'params',
                'type': 'dict',
                'required': False,
                'description': '传递给 Skill 的参数字典'
            }
        ],
        returns={
            'status': 'SUCCESS/FAILED',
            'output': 'Skill 执行的标准输出',
            'file_path': '生成的文件路径（如果有）'
        },
        examples=[
            {
                'description': '生成批量入仓测试 Excel 文件',
                'yaml': '''
- intent: "前置1：生成测试Excel文件"
  action: "bridge_skill"
  params:
    skill_name: "jdbc-warehouse-test"
    action: "generate_excel"
    params:
      database: "dataops_shitingjie"
      table: "test_table_01"
      scenario: "success"
'''
            }
        ]
    )

    def execute(self, context, **params) -> Dict[str, Any]:
        """执行 Skill 桥接"""
        skill_name = params.get('skill_name')
        action = params.get('action')
        
        if 'params' in params and isinstance(params['params'], dict):
            skill_params = params['params']
        else:
            skill_params = {k: v for k, v in params.items() if k not in ('skill_name', 'action')}

        if not skill_name or not action:
            return {
                'status': 'FAILED',
                'message': f'缺少必填参数: skill_name={skill_name}, action={action}'
            }

        # 使用 SkillDiscoverer 获取脚本路径
        script_path = SkillDiscoverer.get_script_path(skill_name, action)
        if not script_path:
            available = SkillDiscoverer.get_available_actions(skill_name)
            msg = f'未找到 action "{action}"'
            if available:
                msg += f'，可用 actions: {", ".join(available)}'
            return {'status': 'FAILED', 'message': msg}

        # 构建命令行参数
        cmd_args = self._build_command_args(skill_name, action, skill_params)

        # 执行脚本
        return self._execute_script(script_path, cmd_args, skill_name, action, skill_params)

    def _build_command_args(self, skill_name: str, action: str, params: Dict) -> list:
        """将参数字典转换为命令行参数"""
        args = []

        # jdbc-warehouse-test batch_workflow 特殊处理
        if skill_name == 'jdbc-warehouse-test' and action == 'batch_workflow':
            env = params.get('env', 'cjjcommon')
            database = params.get('database', 'dataops_shitingjie')
            
            args.extend([env, database])
            
            for key in ['count', 'prefix', 'scenario', 'db_type', 'extract_method', 'deal_method', 'row_count']:
                value = params.get(key)
                if value is not None:
                    args.extend([f'--{key}', str(value)])
            
            args.append('--yes')
            return args

        # generate_excel 特殊处理
        if skill_name == 'jdbc-warehouse-test' and action == 'generate_excel':
            for key in ['database', 'table', 'scenario', 'env']:
                value = params.get(key)
                if value:
                    args.append(value)
            return args

        # 通用参数处理
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, bool):
                if value:
                    args.append(f'--{key.replace("_", "-")}')
                continue
            if isinstance(value, dict):
                import json
                args.extend([f'--{key.replace("_", "-")}', json.dumps(value)])
                continue
            args.extend([f'--{key.replace("_", "-")}', str(value)])

        return args

    def _execute_script(self, script_path: Path, cmd_args: list, skill_name: str, action: str, skill_params: Dict) -> Dict[str, Any]:
        """执行 Python 脚本"""
        env = os.environ.copy()
        scripts_dir = script_path.parent
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))

        cmd = [sys.executable, str(script_path)] + cmd_args

        result = subprocess.run(
            cmd,
            cwd=str(script_path.parent.parent),
            capture_output=True,
            text=True,
            timeout=300
        )

        output = result.stdout
        if result.stderr:
            output += '\n[STDERR]\n' + result.stderr

        # 解析输出中的文件路径
        file_path = self._extract_file_path(output, skill_name, action)

        if result.returncode == 0:
            return {
                'status': 'SUCCESS',
                'message': f'Skill 执行成功',
                'output': output,
                'file_path': file_path
            }
        else:
            return {
                'status': 'FAILED',
                'message': f'Skill 执行失败 (退出码: {result.returncode}): {output[:500]}',
                'output': output,
                'file_path': file_path
            }

    def _extract_file_path(self, output: str, skill_name: str, action: str) -> str:
        """从输出中提取文件路径"""
        for line in output.split('\n'):
            if '文件路径:' in line:
                return line.split('文件路径:')[-1].strip()
            if 'file:' in line.lower() and '.xlsx' in line.lower():
                parts = line.split(':')
                if len(parts) > 1:
                    return parts[-1].strip()
        return None
