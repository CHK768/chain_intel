"""
DDGS 搜索工具封装 — 使用 ddgs 包（多后端自动切换）
"""
from __future__ import annotations

from ddgs import DDGS

from config import DDG_MAX_RESULTS as MAX_RESULTS


def ddg_search(
    query: str,
    max_results: int = MAX_RESULTS,
) -> list[dict]:
    """
    互联网搜索，自动切换后端（Bing/Google/DuckDuckGo HTML）。
    每条结果包含: title, url, content
    """
    results = []
    try:
        with DDGS() as ddgs:
            for item in ddgs.text(query, max_results=max_results):
                title = item.get("title", "")
                url = item.get("href", "") or item.get("url", "")
                body = item.get("body", "") or item.get("content", "")
                if title:
                    results.append({"title": title, "url": url, "content": body})
    except Exception:
        pass
    return results


def search_research_reports(
    company_or_topic: str,
    max_results: int = 5,
) -> list[dict]:
    """搜索券商研报和行业分析"""
    query = f"{company_or_topic} 券商研报 评级 目标价 2024 2025"
    return ddg_search(query, max_results=max_results)


def search_supply_chain(
    product_or_company: str,
    direction: str = "upstream",
    max_results: int = 5,
) -> list[dict]:
    """搜索产业链上下游"""
    dir_kw = "上游原材料 供应商 设备" if direction == "upstream" else "下游应用 客户"
    query = f"{product_or_company} 产业链 {dir_kw}"
    return ddg_search(query, max_results=max_results)


def search_competitors(
    product_or_company: str,
    max_results: int = 5,
) -> list[dict]:
    """搜索竞争对手和替代方案"""
    query = f"{product_or_company} 竞争对手 替代技术 竞品分析"
    return ddg_search(query, max_results=max_results)


def search_emerging_tech(
    tech_domain: str,
    max_results: int = 5,
) -> list[dict]:
    """搜索前沿技术和新工艺"""
    query = f"{tech_domain} 前沿技术 新工艺 突破 2024 2025 专利"
    return ddg_search(query, max_results=max_results)
