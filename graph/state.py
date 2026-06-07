from __future__ import annotations

from typing import TypedDict, Optional, Annotated
from operator import add as list_concat


def _last_value(existing, new):
    """Reducer: 并发更新时取最新值"""
    return new


def _max_value(existing, new):
    """Reducer: 进度只增不减"""
    if existing is None:
        return new
    return max(existing, new)


class Evidence(TypedDict):
    source: str
    url: Optional[str]
    timestamp: str
    confidence: float
    content: str


class SubTaskResult(TypedDict):
    agent: str
    task_id: str
    status: str
    summary: str
    details: str
    evidences: list[Evidence]


class StockRecommendation(TypedDict):
    code: str
    name: str
    rating: str
    target_price_low: Optional[float]
    target_price_high: Optional[float]
    current_price: float
    rationale: str
    risks: list[str]
    confidence: float
    evidences: list[Evidence]


class DebateRecord(TypedDict):
    topic: str
    pro_arguments: list[str]
    con_arguments: list[str]
    rounds: int
    conclusion: str
    confidence: float


class RevisionRequest(TypedDict):
    agent: str
    instruction: str
    round: int


class SharedState(TypedDict):
    user_query: str
    mece_framework: Annotated[str, _last_value]
    sub_tasks: Annotated[list, _last_value]

    results: Annotated[list[SubTaskResult], list_concat]

    revision_requests: Annotated[list, _last_value]
    revision_round: Annotated[int, _last_value]

    conflicts: Annotated[list, _last_value]
    debate_records: Annotated[list, _last_value]

    recommendations: Annotated[list, _last_value]
    final_report: Annotated[str, _last_value]

    current_node: Annotated[str, _last_value]
    progress: Annotated[float, _max_value]
    logs: Annotated[list[dict], list_concat]
    require_human_review: Annotated[bool, _last_value]
    error: Annotated[Optional[str], _last_value]
