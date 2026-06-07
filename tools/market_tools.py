"""
行情数据 API 工具 — AkShare / Tushare / 腾讯财经
"""
from __future__ import annotations

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests as _req
_orig_session_request = _req.Session.request
def _session_request_no_verify(self, method, url, **kwargs):
    kwargs.setdefault("verify", False)
    return _orig_session_request(self, method, url, **kwargs)
_req.Session.request = _session_request_no_verify

import json
import requests
from typing import Optional

import akshare as ak
import pandas as pd


def fetch_realtime_price(codes: list[str]) -> dict[str, dict]:
    """腾讯财经实时行情，返回 {code: {price, change_pct, volume, amount, market_cap}}"""
    if not codes:
        return {}
    query_codes = []
    for c in codes:
        prefix = "sh" if c.startswith("6") else "sz"
        query_codes.append(f"{prefix}{c}")

    url = f"http://qt.gtimg.cn/q={','.join(query_codes)}"
    resp = requests.get(url, timeout=10)
    result = {}
    for line in resp.text.strip().split("\n"):
        if "~" not in line:
            continue
        parts = line.split("~")
        if len(parts) < 46:
            continue
        code = parts[2]
        try:
            result[code] = {
                "name": parts[1],
                "price": float(parts[3]) if parts[3] else None,
                "change_pct": float(parts[32]) if parts[32] else None,
                "volume": float(parts[6]) if parts[6] else None,
                "amount": float(parts[37]) if parts[37] else None,
                "market_cap": float(parts[45]) if parts[45] else None,
                "pe": float(parts[39]) if parts[39] else None,
            }
        except (ValueError, IndexError):
            continue
    return result


def fetch_stock_financials(code: str) -> Optional[dict]:
    """通过 AkShare 获取个股基本财务数据"""
    try:
        df = ak.stock_individual_info_em(symbol=code)
        info = {}
        for _, row in df.iterrows():
            info[row["item"]] = row["value"]
        return info
    except Exception:
        return None


def fetch_sector_fund_flow(sector_name: str) -> Optional[list[dict]]:
    """获取板块资金流向（东方财富）"""
    try:
        df = ak.stock_sector_fund_flow_rank(indicator="今日")
        matched = df[df["名称"].str.contains(sector_name, na=False)]
        if matched.empty:
            return None
        return matched.head(5).to_dict("records")
    except Exception:
        return None


def fetch_stock_history(code: str, period: str = "daily", days: int = 60) -> Optional[list[dict]]:
    """获取个股历史行情"""
    try:
        df = ak.stock_zh_a_hist(symbol=code, period=period, adjust="qfq")
        if df is None or df.empty:
            return None
        df = df.tail(days)
        return df.to_dict("records")
    except Exception:
        return None


def fetch_market_sentiment() -> dict:
    """获取当日市场情绪指标：涨停数、跌停数、涨跌比"""
    try:
        zt_df = ak.stock_zt_pool_em(date=pd.Timestamp.now().strftime("%Y%m%d"))
        dt_df = ak.stock_zt_pool_dtgc_em(date=pd.Timestamp.now().strftime("%Y%m%d"))
        return {
            "zt_count": len(zt_df) if zt_df is not None else 0,
            "dt_count": len(dt_df) if dt_df is not None else 0,
        }
    except Exception:
        return {"zt_count": 0, "dt_count": 0}
