"""
横挖专员 Agent — 替代技术、竞品、竞争格局横向对比
"""
from __future__ import annotations

from agents.base import BaseAgent
from tools.search_tools import ddg_search, search_competitors
from tools.db_tools import query_stock_db, get_stock_concepts


HORIZONTAL_SCANNER_SYSTEM_PROMPT = """你是一位产业横向分析专员。你的任务是横向拓展分析：
- 寻找目标产品/技术的替代方案和竞品
- 对比竞争对手的优劣势（技术路线、市场份额、财务表现）
- 评估替代技术对目标的威胁程度
- 分析竞争格局演变趋势

你有以下工具可用：
1. tavily_search: 通用互联网搜索
2. search_competitors: 专门搜索竞品和替代方案
3. query_stock_db: 查询A股数据库中的相关标的数据

分析要求：
- 竞争对比必须用表格呈现（至少对比3个标的）
- 维度包括：市值、PE、技术路线、市场份额、增速
- 明确标注每个竞品的威胁等级（高/中/低）
- 识别差异化竞争优势"""


class HorizontalScannerAgent(BaseAgent):
    name = "horizontal_scanner"
    role = "横挖专员"
    system_prompt = HORIZONTAL_SCANNER_SYSTEM_PROMPT

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
                "name": "search_competitors",
                "description": "搜索竞争对手和替代方案",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "product_or_company": {"type": "string"},
                        "max_results": {"type": "integer", "default": 5},
                    },
                    "required": ["product_or_company"],
                },
            },
            {
                "name": "query_stock_db",
                "description": "查询A股数据库（只读SQL），可查涨停池、概念、板块统计等",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string", "description": "SQL SELECT 查询"},
                    },
                    "required": ["sql"],
                },
            },
        ]

    def get_tool_handlers(self) -> dict:
        return {
            "ddg_search": lambda query, max_results=5: ddg_search(query, max_results),
            "search_competitors": lambda product_or_company, max_results=5: search_competitors(product_or_company, max_results),
            "query_stock_db": lambda sql: query_stock_db(sql),
        }

    def build_user_message(self, state: dict) -> str:
        task = ""
        for st in state.get("sub_tasks", []):
            if st.get("agent") == "horizontal_scanner":
                task = st.get("task", "")
                break

        revision = ""
        for rr in state.get("revision_requests", []):
            if rr.get("agent") == "horizontal_scanner":
                revision = f"\n\n**项目经理要求你修正/补充以下内容**：\n{rr['instruction']}"
                break

        return f"""研究问题：{state['user_query']}

你的具体任务：{task}

请进行横向对比分析。{revision}

输出要求：
1. 竞争格局概览（市场结构类型：垄断/寡头/充分竞争）
2. 竞品对比表（至少3个标的，含股票代码）
3. 替代技术威胁评估
4. 竞争格局演变趋势预判
5. 差异化优势分析"""
