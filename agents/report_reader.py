"""
研报研究员 Agent — 检索券商研报、行业评级、目标价
"""
from __future__ import annotations

from agents.base import BaseAgent
from tools.search_tools import ddg_search, search_research_reports


REPORT_READER_SYSTEM_PROMPT = """你是一位专业的研报研究员。你的任务是从互联网搜索并整理：
- 券商研报的核心观点和评级
- 行业机构对目标公司/产业的分析
- 目标价区间和投资逻辑
- 风险提示与分歧点

你有以下工具可用：
1. tavily_search: 通用互联网搜索
2. search_research_reports: 专门搜索券商研报

分析要求：
- 标注每条信息的来源机构和发布时间
- 区分"共识观点"和"分歧观点"
- 对分歧点要列出正反双方的论据
- 评级分布统计（强烈推荐/推荐/中性/减持各几家）"""


class ReportReaderAgent(BaseAgent):
    name = "report_reader"
    role = "研报研究员"
    system_prompt = REPORT_READER_SYSTEM_PROMPT

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "ddg_search",
                "description": "DuckDuckGo互联网搜索，返回标题、URL、摘要",
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
                "name": "search_research_reports",
                "description": "专门搜索券商研报和行业分析报告",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "company_or_topic": {"type": "string", "description": "公司名或行业主题"},
                        "max_results": {"type": "integer", "default": 5},
                    },
                    "required": ["company_or_topic"],
                },
            },
        ]

    def get_tool_handlers(self) -> dict:
        return {
            "ddg_search": lambda query, max_results=5: ddg_search(query, max_results),
            "search_research_reports": lambda company_or_topic, max_results=5: search_research_reports(company_or_topic, max_results),
        }

    def build_user_message(self, state: dict) -> str:
        task = ""
        for st in state.get("sub_tasks", []):
            if st.get("agent") == "report_reader":
                task = st.get("task", "")
                break

        revision = ""
        for rr in state.get("revision_requests", []):
            if rr.get("agent") == "report_reader":
                revision = f"\n\n**项目经理要求你修正/补充以下内容**：\n{rr['instruction']}"
                break

        return f"""研究问题：{state['user_query']}

你的具体任务：{task}

请搜索相关研报和行业分析，整理核心观点。{revision}

输出要求：
1. 研报观点汇总表（机构、评级、目标价、核心逻辑）
2. 共识观点（多数机构认同的方向）
3. 分歧点（哪些问题上有对立观点）
4. 风险提示汇总"""
