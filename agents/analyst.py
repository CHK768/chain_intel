"""
股市数据分析师 Agent — 查询股价、财务、估值、资金流向
"""
from __future__ import annotations

from agents.base import BaseAgent
from tools.db_tools import (
    query_stock_db, get_stock_concepts, get_sector_leaders,
    get_stock_daily_pct, get_stock_net_flow, get_sector_net_flow,
    get_zt_records, get_stock_info,
)
from tools.market_tools import fetch_realtime_price, fetch_stock_financials


ANALYST_SYSTEM_PROMPT = """你是一位专业的A股数据分析师。你的任务是利用股市数据库和行情API，分析目标公司及相关标的的：
- 股价走势与技术面
- 财务数据（PE、市值、营收增速）
- 资金流向（主力净流入、板块资金动向）
- 估值对比（同行业PE/PB对比）
- 涨停/跌停统计与市场情绪

你有以下工具可用：
1. query_stock_db: 执行SQL查询股市数据库（含涨停池、概念板块、资金流向等26张表）
2. get_stock_concepts: 查询个股所属概念
3. get_sector_leaders: 查询板块龙头股
4. get_stock_daily_pct: 查询个股涨跌幅
5. get_stock_net_flow: 查询个股主力净流入
6. get_sector_net_flow: 查询板块净流入
7. fetch_realtime_price: 获取实时行情
8. fetch_stock_financials: 获取基本面数据

分析要求：
- 数据必须标注时间和来源
- 对比分析至少3只同板块标的
- 给出明确的数据结论，不要含糊"""


class AnalystAgent(BaseAgent):
    name = "analyst"
    role = "股市数据分析师"
    system_prompt = ANALYST_SYSTEM_PROMPT

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "query_stock_db",
                "description": "执行SQL查询A股数据库(只读)。表包括: zt_records(涨停池), stock_concepts(概念), sector_daily_stats(板块统计), stock_net_flow(资金流), stock_daily_pct(涨跌幅), ths_hot_rank(热度)等。",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string", "description": "SQL SELECT 查询语句"},
                    },
                    "required": ["sql"],
                },
            },
            {
                "name": "get_stock_concepts",
                "description": "查询指定股票代码所属的概念板块列表",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string", "description": "股票代码如 000001"},
                    },
                    "required": ["code"],
                },
            },
            {
                "name": "get_sector_leaders",
                "description": "查询板块近N日龙头股（按涨停次数排序）",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector_name": {"type": "string"},
                        "days": {"type": "integer", "default": 5},
                    },
                    "required": ["sector_name"],
                },
            },
            {
                "name": "fetch_realtime_price",
                "description": "获取多只股票的实时行情（价格、涨跌幅、成交额、市值、PE）",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "codes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "股票代码列表",
                        },
                    },
                    "required": ["codes"],
                },
            },
            {
                "name": "get_stock_net_flow",
                "description": "查询个股近N日主力净流入数据",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "days": {"type": "integer", "default": 5},
                    },
                    "required": ["code"],
                },
            },
            {
                "name": "get_sector_net_flow",
                "description": "查询板块近N日净流入数据",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sector_name": {"type": "string"},
                        "days": {"type": "integer", "default": 5},
                    },
                    "required": ["sector_name"],
                },
            },
        ]

    def get_tool_handlers(self) -> dict:
        return {
            "query_stock_db": lambda sql: query_stock_db(sql),
            "get_stock_concepts": lambda code: get_stock_concepts(code),
            "get_sector_leaders": lambda sector_name, days=5: get_sector_leaders(sector_name, days),
            "fetch_realtime_price": lambda codes: fetch_realtime_price(codes),
            "get_stock_net_flow": lambda code, days=5: get_stock_net_flow(code, days),
            "get_sector_net_flow": lambda sector_name, days=5: get_sector_net_flow(sector_name, days),
        }

    def build_user_message(self, state: dict) -> str:
        task = ""
        for st in state.get("sub_tasks", []):
            if st.get("agent") == "analyst":
                task = st.get("task", "")
                break

        revision = ""
        for rr in state.get("revision_requests", []):
            if rr.get("agent") == "analyst":
                revision = f"\n\n**项目经理要求你修正/补充以下内容**：\n{rr['instruction']}"
                break

        return f"""研究问题：{state['user_query']}

你的具体任务：{task}

请使用工具查询相关数据，进行分析后给出结论。{revision}

输出要求：
1. 关键数据汇总表
2. 数据分析结论（3-5条关键发现）
3. 每条结论的数据证据"""
