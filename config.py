import os
from pathlib import Path

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
TUSHARE_TOKEN = os.environ.get("TUSHARE_TOKEN", "")

DEEPSEEK_BASE_URL = "https://api.deepseek.com/anthropic"

DB_PATH = Path.home() / ".limit_ladder_ths.db"

MODEL_PRIMARY = "deepseek-v4-pro"
MODEL_FAST = "deepseek-v4-flash"

AGENT_MODEL = MODEL_PRIMARY
MAX_TOKENS_MANAGER = 4096
MAX_TOKENS_AGENT = 2048
MAX_TOKENS_FINAL = 8192

MAX_REVISION_ROUNDS = 2

DDG_MAX_RESULTS = 5

AGENT_NAMES = {
    "manager_plan": "项目经理",
    "analyst": "股市数据分析师",
    "report_reader": "研报研究员",
    "deep_diver": "深挖专员",
    "horizontal_scanner": "横挖专员",
    "tech_scout": "新技术侦察员",
    "debater": "辩论协调员",
    "stock_advisor": "A股荐股分析员",
    "gatekeeper": "守门员",
    "manager_review": "项目经理",
    "manager_post_debate": "项目经理",
    "manager_final": "项目经理",
}

AGENT_AVATARS = {
    "manager_plan": "manager.png",
    "analyst": "analyst.png",
    "report_reader": "report_reader.png",
    "deep_diver": "deep_diver.png",
    "horizontal_scanner": "horizontal_scanner.png",
    "tech_scout": "tech_scout.png",
    "debater": "debater.png",
    "stock_advisor": "stock_advisor.png",
    "gatekeeper": "gatekeeper.png",
}
