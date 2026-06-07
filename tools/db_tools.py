"""
SQLite 只读查询工具 — 连接 ~/.limit_ladder_ths.db
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from config import DB_PATH


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def query_stock_db(sql: str, params: tuple = ()) -> list[dict]:
    """执行只读 SQL，返回结果字典列表。拒绝写入操作。"""
    normalized = sql.strip().upper()
    if any(normalized.startswith(kw) for kw in ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE")):
        raise ValueError("Only SELECT queries are allowed")
    with _get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]


def get_stock_concepts(code: str) -> list[str]:
    """查询指定股票所属概念板块名称列表"""
    rows = query_stock_db(
        "SELECT concept_name FROM stock_concepts WHERE code = ?", (code,)
    )
    return [r["concept_name"] for r in rows]


def get_sector_leaders(sector_name: str, days: int = 5) -> list[dict]:
    """查询板块近N日龙头股（按涨停次数排序）"""
    rows = query_stock_db("""
        SELECT z.code, z.name, COUNT(*) as zt_count, MAX(z.consecutive_days) as max_board
        FROM zt_records z
        JOIN stock_concepts sc ON z.code = sc.code AND sc.concept_name = ?
        WHERE z.date >= date('now', ? || ' days')
        GROUP BY z.code, z.name
        ORDER BY zt_count DESC
        LIMIT 20
    """, (sector_name, str(-days)))
    return rows


def get_stock_daily_pct(code: str, days: int = 20) -> list[dict]:
    """查询个股近N日涨跌幅"""
    rows = query_stock_db("""
        SELECT date, pct_change, open_price, close_price, high, low
        FROM stock_daily_pct
        WHERE code = ? ORDER BY date DESC LIMIT ?
    """, (code, days))
    return rows


def get_stock_net_flow(code: str, days: int = 5) -> list[dict]:
    """查询个股近N日主力净流入"""
    rows = query_stock_db("""
        SELECT date, net_amount FROM stock_net_flow
        WHERE code = ? ORDER BY date DESC LIMIT ?
    """, (code, days))
    return rows


def get_sector_net_flow(sector_name: str, days: int = 5) -> list[dict]:
    """查询板块近N日净流入"""
    rows = query_stock_db("""
        SELECT date, net_amount, source FROM sector_net_flow
        WHERE sector_name = ? ORDER BY date DESC LIMIT ?
    """, (sector_name, days))
    return rows


def get_zt_records(date: str) -> list[dict]:
    """查询指定日期涨停池"""
    return query_stock_db(
        "SELECT * FROM zt_records WHERE date = ? ORDER BY consecutive_days DESC", (date,)
    )


def get_stock_info(code: str) -> Optional[dict]:
    """查询个股基本信息（PE、市值等）"""
    rows = query_stock_db("""
        SELECT z.code, z.name, z.price, z.pe, z.float_cap, z.consecutive_days,
               z.first_limit_time, z.seal_amount
        FROM zt_records z WHERE z.code = ?
        ORDER BY z.date DESC LIMIT 1
    """, (code,))
    return rows[0] if rows else None


def list_tables() -> list[str]:
    """列出数据库中所有表名"""
    rows = query_stock_db("SELECT name FROM sqlite_master WHERE type='table'")
    return [r["name"] for r in rows]


def get_table_schema(table_name: str) -> list[dict]:
    """获取表结构"""
    return query_stock_db(f"PRAGMA table_info({table_name})")
