"""
新技术侦察员 Agent — 前沿技术、新工艺、新公司追踪
"""
from __future__ import annotations

from agents.base import BaseAgent
from tools.search_tools import ddg_search, search_emerging_tech


TECH_SCOUT_SYSTEM_PROMPT = """你是一位新技术侦察员。你的任务是追踪前沿技术动态：
- 挖掘新品、新趋势、新格局、新工艺、新流程、新公司、新方案
- 评估技术成熟度（TRL等级：实验室→小试→中试→量产）
- 预估影响时间线（何时可能商业化、何时冲击现有格局）
- 追踪专利布局和学术进展

你有以下工具可用：
1. tavily_search: 通用互联网搜索
2. search_emerging_tech: 专门搜索前沿技术和新工艺

分析要求：
- 按技术成熟度分级列出发现
- 标注关键专利持有者和学术团队
- 评估对现有产业链的颠覆程度（革命性/渐进式/无影响）
- 给出时间线估计（1年内/3年内/5年以上）"""


class TechScoutAgent(BaseAgent):
    name = "tech_scout"
    role = "新技术侦察员"
    system_prompt = TECH_SCOUT_SYSTEM_PROMPT

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "ddg_search",
                "description": "互联网搜索",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "搜索关键词"},
                        "max_results": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "search_emerging_tech",
                "description": "搜索前沿技术、新工艺、技术突破",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "tech_domain": {"type": "string", "description": "技术领域"},
                        "max_results": {"type": "integer", "default": 5},
                    },
                    "required": ["tech_domain"],
                },
            },
        ]

    def get_tool_handlers(self) -> dict:
        return {
            "ddg_search": lambda query, max_results=5: ddg_search(query, max_results),
            "search_emerging_tech": lambda tech_domain, max_results=5: search_emerging_tech(tech_domain, max_results),
        }

    def build_user_message(self, state: dict) -> str:
        task = ""
        for st in state.get("sub_tasks", []):
            if st.get("agent") == "tech_scout":
                task = st.get("task", "")
                break

        revision = ""
        for rr in state.get("revision_requests", []):
            if rr.get("agent") == "tech_scout":
                revision = f"\n\n**项目经理要求你修正/补充以下内容**：\n{rr['instruction']}"
                break

        return f"""研究问题：{state['user_query']}

你的具体任务：{task}

请追踪该领域的前沿技术动态。{revision}

输出要求：
1. 前沿技术清单（按成熟度排序）
2. 每项技术的TRL评级和商业化时间线
3. 关键玩家（专利持有者、研发团队、初创公司）
4. 对现有产业链的颠覆评估
5. 值得关注的A股相关标的"""
