"""
Skill 自动发现模块 - 统一管理 Skill 发现、解析、执行
"""
import os
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional


class SkillDiscoverer:
    """Skill 自动发现器 - 统一入口"""
    
    SKILLS_DIR = Path(__file__).parent.parent / "skills"
    
    SCENARIO_KEYWORDS = {
        'failed_F004': ['元数据未完善', '元数据缺失', 'failed_f004'],
        'failed_F003': ['联动规则冲突', '规则冲突', 'failed_f003'],
        'failed_F002': ['字段格式错误', '非法格式', '格式错误', 'failed_f002'],
        'failed_F001': ['字段缺失', '校验失败', '数据不完整', 'failed_f001'],
    }
    
    @classmethod
    def discover_all_skills(cls) -> List[Dict[str, Any]]:
        """自动发现所有 Skill"""
        skills = []
        
        for skill_dir in cls.SKILLS_DIR.iterdir():
            if not skill_dir.is_dir():
                continue
            if skill_dir.name.startswith('.') or skill_dir.name.startswith('_'):
                continue
            
            skill_info = cls._parse_skill(skill_dir)
            if skill_info:
                skills.append(skill_info)
        
        return skills
    
    @classmethod
    def _parse_skill(cls, skill_dir: Path) -> Optional[Dict[str, Any]]:
        """解析单个 Skill"""
        skill_name = skill_dir.name
        
        skill_json_path = skill_dir / "skill.json"
        if skill_json_path.exists():
            with open(skill_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        skill_md_path = skill_dir / "SKILL.md"
        if skill_md_path.exists():
            return cls._parse_skill_md(skill_dir, skill_md_path)
        
        index_py = skill_dir / "scripts" / "index.py"
        if index_py.exists():
            return {
                'name': skill_name,
                'displayName': skill_name,
                'description': f'Skill: {skill_name}',
                'actions': []
            }
        
        return None
    
    @classmethod
    def _parse_skill_md(cls, skill_dir: Path, md_path: Path) -> Dict[str, Any]:
        """解析 SKILL.md"""
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        in_header = False
        header_lines = []
        
        for line in lines:
            if line.strip() == '---':
                in_header = not in_header
                continue
            if in_header:
                header_lines.append(line)
        
        skill_info = {'name': skill_dir.name, 'actions': []}
        for line in header_lines:
            if line.startswith('name:'):
                skill_info['name'] = line.split(':', 1)[1].strip()
            elif line.startswith('displayName:'):
                skill_info['displayName'] = line.split(':', 1)[1].strip()
            elif line.startswith('description:'):
                skill_info['description'] = line.split(':', 1)[1].strip()
        
        scripts_dir = skill_dir / "scripts"
        if scripts_dir.exists():
            for py_file in scripts_dir.glob("*.py"):
                if py_file.name.startswith('_'):
                    continue
                action_name = py_file.stem
                if action_name not in ['config', 'api_config', 'table_reader']:
                    skill_info['actions'].append({
                        'name': action_name,
                        'description': f'执行 {action_name} 操作'
                    })
        
        return skill_info
    
    @classmethod
    def generate_llm_prompt(cls) -> str:
        """生成 LLM Prompt"""
        skills = cls.discover_all_skills()
        
        prompt_parts = [
            "你是一个测试用例参数解析助手。",
            "根据用户描述的测试需求，解析出需要调用的 Skill 信息。",
            "",
            "可用的 Skill：",
            ""
        ]
        
        for idx, skill in enumerate(skills, 1):
            name = skill.get('name', 'unknown')
            display_name = skill.get('displayName', name)
            description = skill.get('description', '')
            
            prompt_parts.append(f"{idx}. {display_name} ({name})")
            prompt_parts.append(f"   描述: {description}")
            
            actions = skill.get('actions', [])
            if actions:
                action_list = ", ".join([a.get('name', '') for a in actions])
                prompt_parts.append(f"   可用actions: {action_list}")
            
            prompt_parts.append("")
        
        prompt_parts.extend([
            "场景类型映射：",
            "- success: 成功场景",
            "- failed_F001: 字段缺失",
            "- failed_F002: 字段格式错误", 
            "- failed_F003: 联动规则冲突",
            "- failed_F004: 元数据未完善",
            "",
            "返回格式：",
            '{',
            '    "skill_name": "skill名称",',
            '    "action": "action名称",',
            '    "params": {...}',
            '}'
        ])
        
        return "\n".join(prompt_parts)
    
    @classmethod
    def _load_ai_config(cls) -> Dict[str, str]:
        """加载 AI 配置"""
        yaml_config = {}
        
        # 优先从 aitestrunner/.env 文件读取
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('LLM_'):
                        key, value = line.split('=', 1)
                        os.environ[key] = value
        
        config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f).get('ai_service', {}) or {}
        
        return {
            'api_key': os.environ.get('LLM_API_KEY') or yaml_config.get('api_key'),
            'base_url': os.environ.get('LLM_BASE_URL') or yaml_config.get('base_url'),
            'model': os.environ.get('LLM_MODEL') or yaml_config.get('model', 'gpt-4')
        }
    
    @classmethod
    def llm_parse(cls, description: str) -> Dict[str, Any]:
        """调用 LLM 解析自然语言描述"""
        try:
            from openai import OpenAI
            
            config = cls._load_ai_config()
            api_key = config.get('api_key')
            base_url = config.get('base_url', 'https://api.openai.com/v1')
            model = config.get('model', 'gpt-4')
            
            if not api_key or api_key == 'your_api_key':
                return {'error': '未配置 LLM API Key'}
            
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            system_prompt = f"""{cls.generate_llm_prompt()}

**重要规则**：
1. **jdbc-warehouse-test 必须使用 batch_workflow action**
2. 不要指定具体的 table 名称，让 skill 自动生成唯一表名
3. 只返回 JSON 格式，不要其他内容

返回格式：
{{
    "skill_name": "skill名称",
    "action": "batch_workflow", 
    "params": {{}}
}}"""
            
            user_prompt = f"""解析以下测试需求：
{description}

场景类型识别规则：
- 如果描述中包含 "success"、"成功" → scenario: "success"
- 如果描述中包含 "failed_F001" 或 "字段缺失" → scenario: "failed_F001"
- 如果描述中包含 "failed_F002" 或 "字段格式错误" 或 "非法格式" → scenario: "failed_F002"
- 如果描述中包含 "failed_F003" 或 "联动规则冲突" → scenario: "failed_F003"
- 如果描述中包含 "failed_F004" 或 "元数据未完善" → scenario: "failed_F004"

默认参数：
- database: dataops_shitingjie
- env: cjjcommon
- count: 1
- prefix: test_batch

只返回 JSON 格式。"""
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            
            return json.loads(content.strip())
            
        except Exception as e:
            return {'error': str(e)}
    
    @classmethod
    def detect_scenario(cls, description: str) -> str:
        """从描述中识别场景类型"""
        desc = desc_lower = description.lower()
        
        for scenario, keywords in cls.SCENARIO_KEYWORDS.items():
            for kw in keywords:
                if kw in desc_lower:
                    return scenario
        
        return 'success'
    
    @classmethod
    def discover_skills_and_actions(cls) -> Dict[str, List[str]]:
        """自动发现所有 Skill 及其 Action
        
        Returns:
            {
                "jdbc-warehouse-test": ["generate_excel", "batch_workflow", ...],
                "mq-sender": ["send_mq"],
                ...
            }
        """
        result = {}
        
        if not cls.SKILLS_DIR.exists():
            return result
        
        for skill_dir in cls.SKILLS_DIR.iterdir():
            if not skill_dir.is_dir():
                continue
            if skill_dir.name.startswith('.') or skill_dir.name.startswith('_'):
                continue
            
            actions = cls._discover_actions(skill_dir)
            if actions:
                result[skill_dir.name] = actions
        
        return result
    
    @classmethod
    def _discover_actions(cls, skill_dir: Path) -> List[str]:
        """自动发现单个 Skill 的所有 Action"""
        actions = []
        scripts_dir = skill_dir / "scripts"
        
        if not scripts_dir.exists():
            return actions
        
        for py_file in scripts_dir.glob("*.py"):
            if py_file.name.startswith('_'):
                continue
            if py_file.name in ['config.py', 'api_config.py', 'table_reader.py']:
                continue
            
            action_name = py_file.stem
            actions.append(action_name)
        
        return actions
    
    @classmethod
    def get_script_path(cls, skill_name: str, action: str) -> Optional[Path]:
        """获取 Skill 脚本路径 - 自动发现"""
        skill_dir = cls.SKILLS_DIR / skill_name
        if not skill_dir.exists():
            return None
        
        scripts_dir = skill_dir / "scripts"
        if not scripts_dir.exists():
            return None
        
        # 直接根据 action 名称查找脚本
        script_path = scripts_dir / f"{action}.py"
        if script_path.exists():
            return script_path
        
        # 尝试 common 模式
        common_path = scripts_dir / "common.py"
        if common_path.exists():
            return common_path
        
        return None
    
    @classmethod
    def get_available_actions(cls, skill_name: str) -> List[str]:
        """获取 Skill 的可用 actions - 自动发现"""
        skill_dir = cls.SKILLS_DIR / skill_name
        if not skill_dir.exists():
            return []
        
        return cls._discover_actions(skill_dir)
