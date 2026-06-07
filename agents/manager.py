"""
项目经理 Agent — MECE拆解、任务调度、质量审核、Gatekeeper校验
"""
from __future__ import annotations

from agents.base import BaseAgent
from config import MAX_TOKENS_MANAGER


MANAGER_SYSTEM_PROMPT = """你是一位资深的产业链投资调研项目经理。你的职责是：

1. **MECE框架构建**：接收用户的研究问题，提炼出一个MECE（相互独立、完全穷尽）的分析框架。
2. **任务拆解与分配**：将框架中的每个维度拆解为具体的子任务，分配给合适的专员。
3. **质量审核**：审查各专员的输出，检查完整性、逻辑性、证据链。
4. **冲突识别**：发现不同专员之间的矛盾观点，提交辩论协调员裁决。
5. **返工指导**：对质量不达标的输出，给出明确的修正指令要求专员补充。

你同时内嵌"守门员"角色，负责校验：
- 数据新鲜度（数据是否过时）
- 来源权威性（是否有可靠来源）
- 逻辑一致性（结论是否自洽）

输出格式要求：
- 框架拆解时，输出JSON格式的子任务列表
- 审核时，输出通过/返工/冲突的判定及理由
- 最终报告时，输出结构化的Markdown报告"""


class ManagerAgent(BaseAgent):
    name = "manager"
    role = "项目经理"
    system_prompt = MANAGER_SYSTEM_PROMPT

    def __init__(self):
        super().__init__()
        self.max_tokens = MAX_TOKENS_MANAGER

    def get_tools(self) -> list[dict]:
        return []

    def get_tool_handlers(self) -> dict:
        return {}

    def build_user_message(self, state: dict) -> str:
        return ""

    def build_plan_message(self, state: dict) -> str:
        return f"""用户的研究问题是：
{state['user_query']}

请执行以下步骤：
1. 分析这个问题涉及的产业链维度
2. 构建MECE分析框架（确保维度之间相互独立、合起来完全穷尽）
3. 为以下5个专员各分配一个具体的子任务：
   - analyst（股市数据分析师）：负责股价、财务、估值、资金流向数据分析
   - report_reader（研报研究员）：负责检索券商研报、行业评级、目标价
   - deep_diver（深挖专员）：负责向上游追溯原材料、设备、IP供应商
   - horizontal_scanner（横挖专员）：负责横向对比竞品、替代技术、竞争格局
   - tech_scout（新技术侦察员）：负责追踪前沿技术、新工艺、新公司

请用JSON格式输出，包含：
{{
  "mece_framework": "框架描述（每个维度一行）",
  "sub_tasks": [
    {{"agent": "agent_name", "task": "具体任务描述", "focus_points": ["关注点1", "关注点2"]}}
  ]
}}"""

    def build_review_message(self, state: dict) -> str:
        results_text = ""
        for r in state.get("results", []):
            results_text += f"\n### {r['agent']} 的输出：\n{r['summary']}\n"

        return f"""原始研究问题：{state['user_query']}
MECE框架：{state.get('mece_framework', '')}

各专员已完成任务，输出如下：
{results_text}

请执行守门员校验 + 质量审核：
1. **数据新鲜度**：是否有过时的数据？标注哪些需要更新。
2. **来源权威性**：证据链是否可靠？是否有不明来源？
3. **逻辑一致性**：各专员结论是否互相矛盾？
4. **完整性**：MECE框架中是否有维度被遗漏或浅尝辄止？

判定结果用JSON输出：
{{
  "passed_agents": ["通过的agent列表"],
  "revision_requests": [
    {{"agent": "需要返工的agent", "instruction": "具体修正指令"}}
  ],
  "conflicts": [
    {{"topic": "冲突主题", "agent_a": "...", "position_a": "...", "agent_b": "...", "position_b": "..."}}
  ]
}}

当前返工轮次：{state.get('revision_round', 0)} / 2（最多2轮）"""

    def build_final_message(self, state: dict) -> str:
        results_text = ""
        for r in state.get("results", []):
            results_text += f"\n### {r['agent']}：\n{r['details']}\n"

        debate_text = ""
        for d in state.get("debate_records", []):
            debate_text += f"\n**辩题：{d['topic']}**\n结论：{d['conclusion']}\n"

        rec_text = ""
        for rec in state.get("recommendations", []):
            rec_text += f"\n- {rec['code']} {rec['name']}：{rec['rating']}，目标价 {rec.get('target_price_low')}-{rec.get('target_price_high')}\n"

        return f"""请整合所有研究成果，生成最终的结构化投资调研报告。

原始问题：{state['user_query']}
MECE框架：{state.get('mece_framework', '')}

各专员研究成果：{results_text}

辩论结论：{debate_text}

投资建议：{rec_text}

请输出完整的Markdown格式报告，包含：
1. 研究摘要（200字以内）
2. MECE分析框架图
3. 产业链深度分析
4. 横向竞争格局
5. 新技术趋势与影响
6. 投资建议与风险提示
7. 证据来源汇总表

报告要专业、严谨，所有结论都要有数据或证据支撑。"""
