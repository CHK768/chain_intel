"""
Tavily 搜索工具封装
"""
from __future__ import annotations

import os

from tavily import TavilyClient

from config import DDG_MAX_RESULTS as MAX_RESULTS


def _get_client() -> TavilyClient:
    key = os.environ.get("TAVILY_API_KEY", "")
    if not key:
        raise RuntimeError("TAVILY_API_KEY not configured")
    return TavilyClient(api_key=key)


def ddg_search(
    query: str,
    max_results: int = MAX_RESULTS,
) -> list[dict]:
    """
    Tavily 搜索，返回结构化结果列表。
    每条结果包含: title, url, content
    """
    client = _get_client()
    results = []
    try:
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
        )
        for item in response.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
            })
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
