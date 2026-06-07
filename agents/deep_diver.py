"""
深挖专员 Agent — 向上游追溯原材料、设备、IP供应商
"""
from __future__ import annotations

from agents.base import BaseAgent
from tools.search_tools import ddg_search, search_supply_chain


DEEP_DIVER_SYSTEM_PROMPT = """你是一位产业链深挖专员。你的任务是深入分析产业链的纵向结构：
- 从目标产品/公司向上游追溯：原材料→关键设备→核心IP/专利→基础研究
- 识别每一层的关键供应商和技术壁垒
- 评估供应链集中度风险（单一供应商依赖、国产化率等）
- 发掘产业链价值分布（哪个环节利润最厚、议价能力最强）

你有以下工具可用：
1. tavily_search: 通用互联网搜索
2. search_supply_chain: 专门搜索产业链上下游关系

分析要求：
- 画出清晰的产业链层级（至少3层）
- 每层标注代表性公司（含A股标的）
- 识别"卡脖子"环节和国产替代机会
- 标注信息来源和可信度"""


class DeepDiverAgent(BaseAgent):
    name = "deep_diver"
    role = "深挖专员"
    system_prompt = DEEP_DIVER_SYSTEM_PROMPT

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
                "name": "search_supply_chain",
                "description": "搜索产业链上下游关系",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "product_or_company": {"type": "string", "description": "产品或公司名"},
                        "direction": {"type": "string", "enum": ["upstream", "downstream"], "default": "upstream"},
                        "max_results": {"type": "integer", "default": 5},
                    },
                    "required": ["product_or_company"],
                },
            },
        ]

    def get_tool_handlers(self) -> dict:
        return {
            "ddg_search": lambda query, max_results=5: ddg_search(query, max_results),
            "search_supply_chain": lambda product_or_company, direction="upstream", max_results=5: search_supply_chain(product_or_company, direction, max_results),
        }

    def build_user_message(self, state: dict) -> str:
        task = ""
        for st in state.get("sub_tasks", []):
            if st.get("agent") == "deep_diver":
                task = st.get("task", "")
                break

        revision = ""
        for rr in state.get("revision_requests", []):
            if rr.get("agent") == "deep_diver":
                revision = f"\n\n**项目经理要求你修正/补充以下内容**：\n{rr['instruction']}"
                break

        return f"""研究问题：{state['user_query']}

你的具体任务：{task}

请深入追溯产业链上游，给出结构化分析。{revision}

输出要求：
1. 产业链层级图（文字描述，至少3层）
2. 每层关键玩家（公司名+A股代码，如有）
3. 卡脖子环节与国产化率评估
4. 价值链分析（利润分布、议价能力）
5. 供应链风险评估"""
