"""HTML测试报告生成器"""
from typing import Dict, List, Any
from datetime import datetime
import os
import yaml


class HTMLReporter:
    """HTML测试报告生成器"""

    def __init__(self, output_dir: str = "reports"):
        """
        初始化报告生成器

        Args:
            output_dir: 报告输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # 加载业务知识映射
        self.knowledge_mapping = self._load_knowledge_mapping()

    def _load_knowledge_mapping(self) -> Dict:
        """加载业务知识映射配置"""
        try:
            mapping_file = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'config',
                'knowledge_mapping.yaml'
            )
            with open(mapping_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️  加载知识映射配置失败: {e}")
            return {'business_flows': {}, 'business_rules': {}}
    
    def generate_report(self, test_case: Dict, execution_details: Dict, 
                       test_result: Any) -> str:
        """
        生成HTML测试报告
        
        Args:
            test_case: 测试用例信息
            execution_details: 执行详情（包含前置、步骤、断言的详细结果）
            test_result: 测试结果对象
        
        Returns:
            str: 报告文件路径
        """
        # 生成报告文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_case_id = test_case.get('test_case_id', 'UNKNOWN')
        filename = f"{test_case_id}_{timestamp}.html"
        filepath = os.path.join(self.output_dir, filename)
        
        # 生成HTML内容
        html_content = self._generate_html(test_case, execution_details, test_result)
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return filepath
    
    def _generate_html(self, test_case: Dict, execution_details: Dict,
                      test_result: Any) -> str:
        """生成HTML内容"""

        # 提取执行详情
        preconditions = execution_details.get('preconditions', [])
        test_steps = execution_details.get('test_steps', [])
        start_time = execution_details.get('start_time')
        end_time = execution_details.get('end_time')

        # 计算统计信息（包含步骤下的断言）
        total_items = len(preconditions) + len(test_steps)
        total_assertions = 0
        passed_items = sum(1 for p in preconditions if p.get('status') == 'SUCCESS')
        passed_assertions = 0

        for step in test_steps:
            if step.get('status') == 'SUCCESS':
                passed_items += 1
            step_assertions = step.get('assertions', [])
            total_assertions += len(step_assertions)
            passed_assertions += sum(1 for a in step_assertions if a.get('status') == 'PASS')

        total_items += total_assertions
        passed_items += passed_assertions
        failed_items = total_items - passed_items
        
        # 生成HTML
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>测试报告 - {test_case.get('test_case_id', 'N/A')}</title>
    <style>
        {self._get_css_styles()}
    </style>
    <script>
        {self._get_javascript()}
    </script>
</head>
<body>
    <div class="container">
        <!-- 报告头部 -->
        {self._generate_header(test_case, test_result, start_time, end_time)}

        <!-- 执行统计 -->
        {self._generate_statistics(total_items, passed_items, failed_items)}

        <!-- 前置条件 -->
        {self._generate_preconditions_section(preconditions)}

        <!-- 测试步骤（包含步骤下的断言） -->
        {self._generate_test_steps_section(test_steps)}

        <!-- 报告尾部 -->
        {self._generate_footer()}
    </div>
</body>
</html>
"""
        return html
    
    def _get_javascript(self) -> str:
        """获取JavaScript代码"""
        return """
        function toggleItem(id) {
            const content = document.getElementById(id);
            const header = content.previousElementSibling;
            const icon = header.querySelector('.toggle-icon');

            if (content.style.display === 'none') {
                content.style.display = 'block';
                icon.textContent = '▼';
                header.classList.add('expanded');
            } else {
                content.style.display = 'none';
                icon.textContent = '▶';
                header.classList.remove('expanded');
            }
        }

        function expandAll() {
            document.querySelectorAll('.collapsible-content').forEach(content => {
                content.style.display = 'block';
                const header = content.previousElementSibling;
                const icon = header.querySelector('.toggle-icon');
                icon.textContent = '▼';
                header.classList.add('expanded');
            });
        }

        function collapseAll() {
            document.querySelectorAll('.collapsible-content').forEach(content => {
                content.style.display = 'none';
                const header = content.previousElementSibling;
                const icon = header.querySelector('.toggle-icon');
                icon.textContent = '▶';
                header.classList.remove('expanded');
            });
        }

        function toggleRules() {
            const container = document.getElementById('rulesContainer');
            const icon = document.getElementById('toggleIcon');
            const btn = document.getElementById('toggleRulesBtn');

            if (container.style.display === 'none') {
                container.style.display = 'block';
                icon.textContent = '▼';
                btn.classList.add('expanded');
            } else {
                container.style.display = 'none';
                icon.textContent = '▶';
                btn.classList.remove('expanded');
            }
        }
        """

    def _get_css_styles(self) -> str:
        """获取CSS样式"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
        }

        .header h1 {
            font-size: 32px;
            margin-bottom: 30px;
            text-align: center;
        }

        .info-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .info-card {
            background: rgba(255, 255, 255, 0.15);
            padding: 20px;
            border-radius: 12px;
            backdrop-filter: blur(10px);
            display: flex;
            align-items: center;
            gap: 15px;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .info-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
        }

        .card-icon {
            font-size: 36px;
            min-width: 50px;
            text-align: center;
        }

        .card-content {
            flex: 1;
        }

        .card-label {
            font-size: 12px;
            opacity: 0.85;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .card-value {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 3px;
        }

        .card-subtitle {
            font-size: 13px;
            opacity: 0.75;
        }

        .coverage-section {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 12px;
            backdrop-filter: blur(10px);
        }

        .coverage-section h3 {
            margin: 0 0 15px 0;
            font-size: 16px;
            font-weight: 600;
        }

        .flow-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .flow-card {
            padding: 18px 20px;
        }

        .flow-main {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }

        .flow-icon {
            font-size: 24px;
        }

        .flow-info {
            flex: 1;
        }

        .flow-label {
            font-size: 11px;
            color: #6b7280;
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
        }

        .flow-id-name {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .flow-badge {
            font-family: 'Courier New', monospace;
            font-weight: 700;
            font-size: 13px;
            padding: 4px 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 5px;
            white-space: nowrap;
        }

        .flow-name {
            font-size: 15px;
            font-weight: 600;
            color: #1f2937;
        }

        .toggle-rules-btn {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: #f3f4f6;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            color: #374151;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s;
        }

        .toggle-rules-btn:hover {
            background: #e5e7eb;
            border-color: #d1d5db;
        }

        .toggle-icon {
            font-size: 10px;
            transition: transform 0.2s;
        }

        .rules-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
            padding-top: 12px;
            border-top: 1px solid #e5e7eb;
        }

        .rule-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            background: #f9fafb;
            border-radius: 6px;
            border-left: 3px solid #667eea;
            transition: all 0.2s;
        }

        .rule-item:hover {
            background: #f3f4f6;
            transform: translateX(3px);
            border-left-color: #764ba2;
        }

        .rule-badge {
            font-family: 'Courier New', monospace;
            font-weight: 700;
            font-size: 11px;
            padding: 4px 10px;
            background: #e0e7ff;
            color: #4f46e5;
            border-radius: 4px;
            white-space: nowrap;
        }

        .rule-text {
            color: #4b5563;
            font-size: 13px;
            flex: 1;
        }

        .no-rules {
            text-align: center;
            color: #9ca3af;
            font-style: italic;
            padding: 20px;
            font-size: 13px;
        }

        .status-pass {
            color: #10b981;
        }

        .status-fail {
            color: #ef4444;
        }

        .statistics {
            padding: 30px;
            background: #f9fafb;
        }

        .statistics h2 {
            color: #1f2937;
            margin-bottom: 20px;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }

        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }

        .stat-card.stat-success {
            border-left-color: #10b981;
        }

        .stat-card.stat-fail {
            border-left-color: #ef4444;
        }

        .stat-card.stat-rate {
            border-left-color: #f59e0b;
        }

        .stat-number {
            font-size: 36px;
            font-weight: bold;
            color: #1f2937;
            margin-bottom: 5px;
        }

        .stat-label {
            font-size: 14px;
            color: #6b7280;
        }

        .section {
            padding: 30px;
            border-top: 1px solid #e5e7eb;
        }

        .section h2 {
            color: #1f2937;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .section-controls {
            display: flex;
            gap: 10px;
        }

        .btn {
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.2s;
        }

        .btn-expand {
            background: #10b981;
            color: white;
        }

        .btn-expand:hover {
            background: #059669;
        }

        .btn-collapse {
            background: #6b7280;
            color: white;
        }

        .btn-collapse:hover {
            background: #4b5563;
        }

        .execution-items {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .execution-item {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            overflow: hidden;
            transition: all 0.3s ease;
        }

        .execution-item.item-success {
            border-left: 4px solid #10b981;
        }

        .execution-item.item-fail {
            border-left: 4px solid #ef4444;
        }

        .execution-item.item-unknown {
            border-left: 4px solid #f59e0b;
        }

        .collapsible-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 20px;
            background: #f9fafb;
            cursor: pointer;
            user-select: none;
            transition: background 0.2s;
        }

        .collapsible-header:hover {
            background: #f3f4f6;
        }

        .collapsible-header.expanded {
            background: #e5e7eb;
        }

        .header-left {
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;
        }

        .toggle-icon {
            font-size: 12px;
            color: #6b7280;
            min-width: 16px;
        }

        .item-index {
            font-weight: bold;
            color: #1f2937;
            min-width: 80px;
        }

        .item-intent {
            color: #374151;
            flex: 1;
        }

        .item-status {
            font-weight: bold;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            background: white;
        }

        .collapsible-content {
            display: none;
            padding: 20px;
            border-top: 1px solid #e5e7eb;
        }

        .item-body {
            padding: 0;
        }

        .sub-assertions {
            margin-top: 15px;
            padding-left: 20px;
            border-left: 3px solid #e5e7eb;
        }

        .sub-assertions-title {
            font-weight: bold;
            color: #6b7280;
            margin-bottom: 10px;
            font-size: 14px;
        }

        .item-row {
            display: flex;
            margin-bottom: 10px;
            align-items: flex-start;
        }

        .item-label {
            min-width: 100px;
            font-weight: bold;
            color: #6b7280;
        }

        .item-value {
            flex: 1;
            color: #1f2937;
        }

        .item-value code {
            background: #f3f4f6;
            padding: 2px 8px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            color: #667eea;
        }

        .item-details {
            margin-top: 15px;
        }

        details {
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            padding: 10px;
            background: #f9fafb;
        }

        summary {
            cursor: pointer;
            font-weight: bold;
            color: #667eea;
            user-select: none;
        }

        summary:hover {
            color: #764ba2;
        }

        .details-content {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #e5e7eb;
        }

        pre {
            background: #1f2937;
            color: #10b981;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 13px;
            line-height: 1.5;
        }

        .error-message {
            margin-top: 15px;
            padding: 15px;
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 6px;
            color: #991b1b;
        }

        .error-message strong {
            display: block;
            margin-bottom: 10px;
        }

        .error-message pre {
            background: #fee2e2;
            color: #991b1b;
            margin-top: 10px;
        }

        .footer {
            padding: 20px 30px;
            background: #f9fafb;
            border-top: 1px solid #e5e7eb;
            text-align: center;
            color: #6b7280;
            font-size: 14px;
        }

        .footer p {
            margin: 5px 0;
        }
"""
    
    def _generate_header(self, test_case: Dict, test_result: Any,
                        start_time: datetime, end_time: datetime) -> str:
        """生成报告头部"""
        status_class = 'status-pass' if test_result.status == 'PASS' else 'status-fail'
        status_icon = '✅' if test_result.status == 'PASS' else '❌'

        start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S") if start_time else 'N/A'
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S") if end_time else 'N/A'

        # 生成业务覆盖表格
        coverage_table = self._generate_coverage_table(test_case)

        return f"""
        <div class="header">
            <h1>🧪 AI测试框架 - 测试报告</h1>

            <!-- 基本信息卡片 -->
            <div class="info-cards">
                <div class="info-card">
                    <div class="card-icon">📋</div>
                    <div class="card-content">
                        <div class="card-label">测试用例</div>
                        <div class="card-value">{test_case.get('test_case_id', 'N/A')}</div>
                        <div class="card-subtitle">{test_case.get('test_name', 'N/A')}</div>
                    </div>
                </div>

                <div class="info-card">
                    <div class="card-icon">{status_icon}</div>
                    <div class="card-content">
                        <div class="card-label">执行状态</div>
                        <div class="card-value {status_class}">{test_result.status}</div>
                        <div class="card-subtitle">耗时 {test_result.execution_time:.2f} 秒</div>
                    </div>
                </div>

                <div class="info-card">
                    <div class="card-icon">⏰</div>
                    <div class="card-content">
                        <div class="card-label">执行时间</div>
                        <div class="card-value">{start_time_str}</div>
                        <div class="card-subtitle">至 {end_time_str}</div>
                    </div>
                </div>
            </div>

            <!-- 业务覆盖信息 -->
            {coverage_table}
        </div>
        """

    def _generate_coverage_table(self, test_case: Dict) -> str:
        """生成业务覆盖信息（简洁嵌套布局）"""
        # 获取业务流程
        flow_id = test_case.get('business_flow', '')
        flow_name = self.knowledge_mapping.get('business_flows', {}).get(flow_id, '未知流程')

        # 获取业务规则
        rule_ids = test_case.get('business_rules', [])
        rules_html = ""
        for rule_id in rule_ids:
            rule_name = self.knowledge_mapping.get('business_rules', {}).get(rule_id, '未知规则')
            rules_html += f"""
            <div class="rule-item">
                <span class="rule-badge">{rule_id}</span>
                <span class="rule-text">{rule_name}</span>
            </div>
            """

        if not rules_html:
            rules_html = '<div class="no-rules">暂无业务规则</div>'

        return f"""
        <div class="coverage-section">
            <h3>📊 业务覆盖范围</h3>
            <div class="flow-container">
                <div class="flow-card">
                    <!-- 业务流程头部 -->
                    <div class="flow-main">
                        <div class="flow-icon">🔄</div>
                        <div class="flow-info">
                            <div class="flow-label">业务流程</div>
                            <div class="flow-id-name">
                                <span class="flow-badge">{flow_id}</span>
                                <span class="flow-name">{flow_name}</span>
                            </div>
                        </div>
                        <button class="toggle-rules-btn" onclick="toggleRules()" id="toggleRulesBtn">
                            <span class="toggle-icon" id="toggleIcon">▼</span>
                            <span class="toggle-text">业务规则 ({len(rule_ids)})</span>
                        </button>
                    </div>

                    <!-- 业务规则列表（可折叠） -->
                    <div class="rules-list" id="rulesContainer">
                        {rules_html}
                    </div>
                </div>
            </div>
        </div>
        """

    def _generate_statistics(self, total: int, passed: int, failed: int) -> str:
        """生成执行统计"""
        pass_rate = (passed / total * 100) if total > 0 else 0

        return f"""
        <div class="statistics">
            <h2>📊 执行统计</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{total}</div>
                    <div class="stat-label">总执行项</div>
                </div>
                <div class="stat-card stat-success">
                    <div class="stat-number">{passed}</div>
                    <div class="stat-label">成功</div>
                </div>
                <div class="stat-card stat-fail">
                    <div class="stat-number">{failed}</div>
                    <div class="stat-label">失败</div>
                </div>
                <div class="stat-card stat-rate">
                    <div class="stat-number">{pass_rate:.1f}%</div>
                    <div class="stat-label">通过率</div>
                </div>
            </div>
        </div>
        """

    def _generate_preconditions_section(self, preconditions: List[Dict]) -> str:
        """生成前置条件部分"""
        if not preconditions:
            return ""

        items_html = ""
        for i, item in enumerate(preconditions):
            items_html += self._generate_collapsible_item(i + 1, item, "前置条件", f"precond_{i}")

        return f"""
        <div class="section">
            <h2>
                <span>🔧 前置条件 ({len(preconditions)}项)</span>
                <div class="section-controls">
                    <button class="btn btn-expand" onclick="expandAll()">全部展开</button>
                    <button class="btn btn-collapse" onclick="collapseAll()">全部收起</button>
                </div>
            </h2>
            <div class="execution-items">
                {items_html}
            </div>
        </div>
        """

    def _generate_test_steps_section(self, test_steps: List[Dict]) -> str:
        """生成测试步骤部分（包含步骤下的断言）"""
        if not test_steps:
            return ""

        items_html = ""
        for i, step in enumerate(test_steps):
            items_html += self._generate_step_with_assertions(i + 1, step, f"step_{i}")

        return f"""
        <div class="section">
            <h2>
                <span>🚀 测试步骤 ({len(test_steps)}项)</span>
                <div class="section-controls">
                    <button class="btn btn-expand" onclick="expandAll()">全部展开</button>
                    <button class="btn btn-collapse" onclick="collapseAll()">全部收起</button>
                </div>
            </h2>
            <div class="execution-items">
                {items_html}
            </div>
        </div>
        """

    def _generate_step_with_assertions(self, index: int, step: Dict, step_id: str) -> str:
        """生成包含断言的测试步骤"""
        # 判断状态
        status = step.get('status', 'UNKNOWN')
        if status in ['SUCCESS', 'PASS']:
            status_class = 'item-success'
            status_icon = '✅'
            status_text = '成功'
        elif status in ['FAIL', 'FAILURE']:
            status_class = 'item-fail'
            status_icon = '❌'
            status_text = '失败'
        else:
            status_class = 'item-unknown'
            status_icon = '⚠️'
            status_text = status

        intent = step.get('intent', 'N/A')

        # 生成步骤内容
        step_content = self._generate_item_content(step)

        # 生成步骤下的断言
        assertions = step.get('assertions', [])
        assertions_html = ""
        if assertions:
            assertions_items = ""
            for j, assertion in enumerate(assertions):
                assertions_items += self._generate_collapsible_item(
                    j + 1, assertion, "断言", f"{step_id}_assert_{j}"
                )
            assertions_html = f"""
            <div class="sub-assertions">
                <div class="sub-assertions-title">🔍 步骤断言 ({len(assertions)}个)</div>
                <div class="execution-items">
                    {assertions_items}
                </div>
            </div>
            """

        return f"""
        <div class="execution-item {status_class}">
            <div class="collapsible-header" onclick="toggleItem('{step_id}_content')">
                <div class="header-left">
                    <span class="toggle-icon">▶</span>
                    <span class="item-index">步骤 #{index}</span>
                    <span class="item-intent">{self._escape_html(intent)}</span>
                </div>
                <div class="item-status">{status_icon} {status_text}</div>
            </div>
            <div id="{step_id}_content" class="collapsible-content">
                {step_content}
                {assertions_html}
            </div>
        </div>
        """

    def _generate_collapsible_item(self, index: int, item: Dict, item_type: str, item_id: str) -> str:
        """生成可折叠的执行项"""
        # 判断状态
        status = item.get('status', 'UNKNOWN')
        if status in ['SUCCESS', 'PASS']:
            status_class = 'item-success'
            status_icon = '✅'
            status_text = '成功'
        elif status in ['FAIL', 'FAILURE']:
            status_class = 'item-fail'
            status_icon = '❌'
            status_text = '失败'
        else:
            status_class = 'item-unknown'
            status_icon = '⚠️'
            status_text = status

        intent = item.get('intent', 'N/A')
        content = self._generate_item_content(item)

        return f"""
        <div class="execution-item {status_class}">
            <div class="collapsible-header" onclick="toggleItem('{item_id}_content')">
                <div class="header-left">
                    <span class="toggle-icon">▶</span>
                    <span class="item-index">{item_type} #{index}</span>
                    <span class="item-intent">{self._escape_html(intent)}</span>
                </div>
                <div class="item-status">{status_icon} {status_text}</div>
            </div>
            <div id="{item_id}_content" class="collapsible-content">
                {content}
            </div>
        </div>
        """

    def _generate_item_content(self, item: Dict) -> str:
        """生成执行项的详细内容"""
        action = item.get('action', 'N/A')
        params = item.get('params', {})
        result = item.get('result', {})
        error = item.get('error', '')
        start_time = item.get('start_time', '')
        end_time = item.get('end_time', '')
        duration = item.get('duration', 0)

        # 格式化时间
        start_time_str = start_time.strftime("%H:%M:%S.%f")[:-3] if isinstance(start_time, datetime) else str(start_time)
        end_time_str = end_time.strftime("%H:%M:%S.%f")[:-3] if isinstance(end_time, datetime) else str(end_time)

        # 格式化参数
        params_html = self._format_dict_to_html(params)
        result_html = self._format_dict_to_html(result)

        # 错误信息
        error_html = ""
        if error:
            error_html = f"""
            <div class="error-message">
                <strong>❌ 失败原因:</strong>
                <pre>{self._escape_html(str(error))}</pre>
            </div>
            """

        return f"""
        <div class="item-row">
            <span class="item-label">使用动作:</span>
            <span class="item-value"><code>{action}</code></span>
        </div>
        <div class="item-row">
            <span class="item-label">开始时间:</span>
            <span class="item-value">{start_time_str}</span>
        </div>
        <div class="item-row">
            <span class="item-label">结束时间:</span>
            <span class="item-value">{end_time_str}</span>
        </div>
        <div class="item-row">
            <span class="item-label">执行耗时:</span>
            <span class="item-value">{duration:.3f} 秒</span>
        </div>
        <div class="item-details">
            <details>
                <summary>📋 输入参数</summary>
                <div class="details-content">
                    {params_html}
                </div>
            </details>
        </div>
        <div class="item-details">
            <details>
                <summary>📤 执行结果</summary>
                <div class="details-content">
                    {result_html}
                </div>
            </details>
        </div>
        {error_html}
        """

    def _format_dict_to_html(self, data: Any) -> str:
        """将字典格式化为HTML"""
        if not data:
            return "<pre>无</pre>"

        import json
        try:
            formatted = json.dumps(data, ensure_ascii=False, indent=2)
            return f"<pre>{self._escape_html(formatted)}</pre>"
        except:
            return f"<pre>{self._escape_html(str(data))}</pre>"

    def _escape_html(self, text: str) -> str:
        """转义HTML特殊字符"""
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))

    def _generate_footer(self) -> str:
        """生成报告尾部"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""
        <div class="footer">
            <p>报告生成时间: {current_time}</p>
            <p>AI测试框架 v1.0 | Powered by knowtest_ai</p>
        </div>
        """

