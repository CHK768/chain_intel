"""
A股荐股分析员 Agent — 基于所有研究输出筛选投资标的
"""
from __future__ import annotations

from agents.base import BaseAgent
from tools.db_tools import query_stock_db, get_stock_concepts
from tools.market_tools import fetch_realtime_price


STOCK_ADVISOR_SYSTEM_PROMPT = """你是一位A股投资顾问。你的任务是基于前序所有调研结论，筛选具体的A股投资标的。

你需要：
1. 从产业链分析、竞争格局、技术趋势中提取投资逻辑
2. 筛选相关A股标的（代码、名称）
3. 给出投资评级：强烈推荐 / 推荐 / 中性 / 规避
4. 给出目标价区间（基于PE/PEG/DCF等估值方法）
5. 列出核心风险点

你有以下工具可用：
1. query_stock_db: 查询A股数据库
2. fetch_realtime_price: 获取实时行情数据

评级标准：
- 强烈推荐：预期收益>30%，逻辑确定性高，催化剂明确
- 推荐：预期收益15-30%，逻辑清晰
- 中性：预期收益0-15%，或不确定性较大
- 规避：明确看空因素，下行风险>上行空间

投资建议必须附带：
- 买入时机建议
- 止损位设置
- 持仓周期建议
- 仓位配置建议"""


class StockAdvisorAgent(BaseAgent):
    name = "stock_advisor"
    role = "A股荐股分析员"
    system_prompt = STOCK_ADVISOR_SYSTEM_PROMPT

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "query_stock_db",
                "description": "查询A股数据库，含涨停池、概念板块、资金流向等数据",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string", "description": "SQL SELECT 查询"},
                    },
                    "required": ["sql"],
                },
            },
            {
                "name": "fetch_realtime_price",
                "description": "获取多只股票实时行情（价格、涨跌幅、市值、PE）",
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
        ]

    def get_tool_handlers(self) -> dict:
        return {
            "query_stock_db": lambda sql: query_stock_db(sql),
            "fetch_realtime_price": lambda codes: fetch_realtime_price(codes),
        }

    def build_user_message(self, state: dict) -> str:
        results_text = ""
        for r in state.get("results", []):
            results_text += f"\n### {r['agent']}：\n{r['summary']}\n"

        debate_text = ""
        for d in state.get("debate_records", []):
            debate_text += f"\n辩题：{d['topic']}\n结论：{d['conclusion']}（置信度{d['confidence']}）\n"

        return f"""研究问题：{state['user_query']}

以下是各专员的研究结论：
{results_text}

辩论结论：
{debate_text if debate_text else "无冲突辩论"}

请基于以上所有信息：
1. 筛选最相关的A股标的（3-8只）
2. 用工具查询其最新行情数据
3. 给出每只标的的投资评级和目标价

输出JSON格式：
{{
  "recommendations": [
    {{
      "code": "股票代码",
      "name": "股票名称",
      "rating": "强烈推荐/推荐/中性/规避",
      "target_price_low": 目标价下限,
      "target_price_high": 目标价上限,
      "current_price": 当前价格,
      "rationale": "推荐理由（100字以内）",
      "risks": ["风险1", "风险2"],
      "buy_timing": "买入时机建议",
      "stop_loss": "止损位",
      "holding_period": "持仓周期",
      "position_size": "仓位建议"
    }}
  ],
  "portfolio_strategy": "整体组合策略建议"
}}"""
