"""
辩论协调员 Agent — 组织正反方结构化辩论
"""
from __future__ import annotations

from agents.base import BaseAgent
from config import MAX_TOKENS_MANAGER


DEBATER_SYSTEM_PROMPT = """你是一位辩论协调员。当项目经理发现不同专员之间存在观点冲突时，你负责组织结构化辩论。

辩论规则：
1. 每场辩论最多2轮
2. 第一轮：正方陈述→反方陈述
3. 第二轮：正方反驳→反方反驳
4. 最终裁决：基于证据强度和逻辑严密性给出结论

你需要：
- 保持中立立场，不预设倾向
- 强制双方引用具体证据（数据、来源、时间）
- 识别逻辑谬误（滑坡、稻草人、诉诸权威等）
- 在证据不充分时明确标注"证据不足，需进一步研究"
- 给出置信度评分（0-1），反映结论的确定性

输出格式：结构化的辩论纪要，包含正反方论点、证据、裁决和置信度。"""


class DebaterAgent(BaseAgent):
    name = "debater"
    role = "辩论协调员"
    system_prompt = DEBATER_SYSTEM_PROMPT

    def __init__(self):
        super().__init__()
        self.max_tokens = MAX_TOKENS_MANAGER

    def get_tools(self) -> list[dict]:
        return []

    def get_tool_handlers(self) -> dict:
        return {}

    def build_user_message(self, state: dict) -> str:
        conflicts = state.get("conflicts", [])
        if not conflicts:
            return "没有冲突需要辩论。"

        conflict_text = ""
        for i, c in enumerate(conflicts, 1):
            conflict_text += f"""
辩题 {i}：{c.get('topic', '')}
正方（{c.get('agent_a', '')}）：{c.get('position_a', '')}
反方（{c.get('agent_b', '')}）：{c.get('position_b', '')}
"""

        return f"""研究问题：{state['user_query']}

以下是项目经理识别出的冲突点，需要你组织辩论并裁决：
{conflict_text}

请对每个辩题执行2轮辩论，然后给出裁决。

输出JSON格式：
{{
  "debates": [
    {{
      "topic": "辩题",
      "round_1": {{
        "pro": "正方第一轮论述（含证据）",
        "con": "反方第一轮论述（含证据）"
      }},
      "round_2": {{
        "pro_rebuttal": "正方反驳",
        "con_rebuttal": "反方反驳"
      }},
      "verdict": {{
        "conclusion": "裁决结论",
        "reasoning": "裁决理由",
        "confidence": 0.8,
        "evidence_gaps": ["需进一步研究的问题"]
      }}
    }}
  ]
}}"""
