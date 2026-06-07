"""
LangGraph 主状态图 — 节点定义、边、条件路由、返工循环
"""
from __future__ import annotations

import json
import asyncio
import time
from typing import Any

from langgraph.graph import StateGraph, START, END

from graph.state import SharedState, SubTaskResult, RevisionRequest
from agents.manager import ManagerAgent
from agents.analyst import AnalystAgent
from agents.report_reader import ReportReaderAgent
from agents.deep_diver import DeepDiverAgent
from agents.horizontal_scanner import HorizontalScannerAgent
from agents.tech_scout import TechScoutAgent
from agents.debater import DebaterAgent
from agents.stock_advisor import StockAdvisorAgent
from config import MAX_REVISION_ROUNDS


_manager = ManagerAgent()
_analyst = AnalystAgent()
_report_reader = ReportReaderAgent()
_deep_diver = DeepDiverAgent()
_horizontal_scanner = HorizontalScannerAgent()
_tech_scout = TechScoutAgent()
_debater = DebaterAgent()
_stock_advisor = StockAdvisorAgent()

_progress_callback = None


def set_progress_callback(cb):
    global _progress_callback
    _progress_callback = cb


def _emit(node: str, progress: float, msg: str = ""):
    if _progress_callback:
        _progress_callback(node, progress, msg)


def _parse_json_from_text(text: str) -> dict:
    """从 LLM 输出中提取 JSON"""
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass
    return {}


# ─────────────── 节点函数 ───────────────

def manager_plan_node(state: SharedState) -> dict:
    """PM 接收问题，构建 MECE 框架，拆解子任务"""
    _emit("manager_plan", 0.05, "PM 正在构建 MECE 分析框架...")

    msg = _manager.build_plan_message(state)
    messages = [{"role": "user", "content": msg}]
    response = _manager.client.messages.create(
        model=_manager.model,
        max_tokens=_manager.max_tokens,
        system=_manager.system_prompt,
        messages=messages,
    )
    text = "".join(b.text for b in response.content if hasattr(b, "text"))
    parsed = _parse_json_from_text(text)

    framework = parsed.get("mece_framework", text[:500])
    sub_tasks = parsed.get("sub_tasks", [])

    if not sub_tasks:
        sub_tasks = [
            {"agent": "analyst", "task": f"分析与'{state['user_query']}'相关的A股数据"},
            {"agent": "report_reader", "task": f"搜索'{state['user_query']}'相关研报"},
            {"agent": "deep_diver", "task": f"深挖'{state['user_query']}'产业链上游"},
            {"agent": "horizontal_scanner", "task": f"横向分析'{state['user_query']}'竞品格局"},
            {"agent": "tech_scout", "task": f"追踪'{state['user_query']}'前沿技术"},
        ]

    return {
        "mece_framework": framework,
        "sub_tasks": sub_tasks,
        "current_node": "manager_plan",
        "progress": 0.1,
        "logs": [{"time": time.strftime("%H:%M:%S"), "agent": "manager", "msg": "MECE框架构建完成"}],
    }


def _run_agent(agent, state: SharedState, agent_name: str) -> SubTaskResult:
    """通用 agent 执行封装"""
    try:
        result = agent.execute(state)
        return SubTaskResult(
            agent=agent_name,
            task_id=f"{agent_name}_{int(time.time())}",
            status="done",
            summary=result.get("summary", ""),
            details=result.get("details", ""),
            evidences=result.get("evidences", []),
        )
    except Exception as e:
        return SubTaskResult(
            agent=agent_name,
            task_id=f"{agent_name}_{int(time.time())}",
            status="error",
            summary=f"Error: {str(e)}",
            details=str(e),
            evidences=[],
        )


def analyst_node(state: SharedState) -> dict:
    _emit("analyst", 0.2, "数据分析师正在查询股市数据...")
    result = _run_agent(_analyst, state, "analyst")
    return {
        "results": [result],
        "current_node": "analyst",
        "progress": 0.25,
        "logs": [{"time": time.strftime("%H:%M:%S"), "agent": "analyst", "msg": result["summary"][:100]}],
    }


def report_reader_node(state: SharedState) -> dict:
    _emit("report_reader", 0.2, "研报研究员正在检索研报...")
    result = _run_agent(_report_reader, state, "report_reader")
    return {
        "results": [result],
        "current_node": "report_reader",
        "progress": 0.3,
        "logs": [{"time": time.strftime("%H:%M:%S"), "agent": "report_reader", "msg": result["summary"][:100]}],
    }


def deep_diver_node(state: SharedState) -> dict:
    _emit("deep_diver", 0.2, "深挖专员正在追溯产业链...")
    result = _run_agent(_deep_diver, state, "deep_diver")
    return {
        "results": [result],
        "current_node": "deep_diver",
        "progress": 0.35,
        "logs": [{"time": time.strftime("%H:%M:%S"), "agent": "deep_diver", "msg": result["summary"][:100]}],
    }


def horizontal_scanner_node(state: SharedState) -> dict:
    _emit("horizontal_scanner", 0.2, "横挖专员正在分析竞争格局...")
    result = _run_agent(_horizontal_scanner, state, "horizontal_scanner")
    return {
        "results": [result],
        "current_node": "horizontal_scanner",
        "progress": 0.4,
        "logs": [{"time": time.strftime("%H:%M:%S"), "agent": "horizontal_scanner", "msg": result["summary"][:100]}],
    }


def tech_scout_node(state: SharedState) -> dict:
    _emit("tech_scout", 0.2, "新技术侦察员正在追踪前沿技术...")
    result = _run_agent(_tech_scout, state, "tech_scout")
    return {
        "results": [result],
        "current_node": "tech_scout",
        "progress": 0.45,
        "logs": [{"time": time.strftime("%H:%M:%S"), "agent": "tech_scout", "msg": result["summary"][:100]}],
    }


def manager_review_node(state: SharedState) -> dict:
    """PM 审核所有输出，Gatekeeper 校验"""
    _emit("manager_review", 0.55, "PM 正在审核各专员输出...")

    msg = _manager.build_review_message(state)
    messages = [{"role": "user", "content": msg}]
    response = _manager.client.messages.create(
        model=_manager.model,
        max_tokens=_manager.max_tokens,
        system=_manager.system_prompt,
        messages=messages,
    )
    text = "".join(b.text for b in response.content if hasattr(b, "text"))
    parsed = _parse_json_from_text(text)

    revision_requests = []
    conflicts = []
    current_round = state.get("revision_round", 0)

    if current_round < MAX_REVISION_ROUNDS:
        for rr in parsed.get("revision_requests", []):
            revision_requests.append(RevisionRequest(
                agent=rr["agent"],
                instruction=rr["instruction"],
                round=current_round + 1,
            ))

    for c in parsed.get("conflicts", []):
        conflicts.append(c)

    return {
        "revision_requests": revision_requests,
        "revision_round": current_round + (1 if revision_requests else 0),
        "conflicts": conflicts,
        "current_node": "manager_review",
        "progress": 0.6,
        "logs": [{"time": time.strftime("%H:%M:%S"), "agent": "manager",
                  "msg": f"审核完成：{len(revision_requests)}项返工，{len(conflicts)}项冲突"}],
    }


def debater_node(state: SharedState) -> dict:
    """辩论协调员处理冲突"""
    _emit("debater", 0.65, "辩论协调员正在组织辩论...")

    result = _debater.execute(state)
    text = result.get("details", "")
    parsed = _parse_json_from_text(text)

    debate_records = []
    for d in parsed.get("debates", []):
        verdict = d.get("verdict", {})
        debate_records.append({
            "topic": d.get("topic", ""),
            "pro_arguments": [d.get("round_1", {}).get("pro", "")],
            "con_arguments": [d.get("round_1", {}).get("con", "")],
            "rounds": 2,
            "conclusion": verdict.get("conclusion", text[:200]),
            "confidence": verdict.get("confidence", 0.5),
        })

    if not debate_records:
        debate_records.append({
            "topic": state["conflicts"][0].get("topic", "") if state.get("conflicts") else "",
            "pro_arguments": [],
            "con_arguments": [],
            "rounds": 2,
            "conclusion": text[:300],
            "confidence": 0.6,
        })

    return {
        "debate_records": debate_records,
        "current_node": "debater",
        "progress": 0.7,
        "logs": [{"time": time.strftime("%H:%M:%S"), "agent": "debater",
                  "msg": f"辩论完成，{len(debate_records)}个议题已裁决"}],
    }


def manager_post_debate_node(state: SharedState) -> dict:
    """PM 采纳辩论结论"""
    _emit("manager_post_debate", 0.72, "PM 正在采纳辩论结论...")
    return {
        "conflicts": [],
        "current_node": "manager_post_debate",
        "progress": 0.73,
        "logs": [{"time": time.strftime("%H:%M:%S"), "agent": "manager", "msg": "辩论结论已采纳"}],
    }


def stock_advisor_node(state: SharedState) -> dict:
    """荐股分析员筛选标的"""
    _emit("stock_advisor", 0.75, "荐股分析员正在筛选标的...")

    result = _stock_advisor.execute(state)
    text = result.get("details", "")
    parsed = _parse_json_from_text(text)

    recommendations = parsed.get("recommendations", [])

    return {
        "recommendations": recommendations,
        "current_node": "stock_advisor",
        "progress": 0.85,
        "logs": [{"time": time.strftime("%H:%M:%S"), "agent": "stock_advisor",
                  "msg": f"筛选出{len(recommendations)}只标的"}],
    }


def manager_final_node(state: SharedState) -> dict:
    """PM 整合最终报告"""
    _emit("manager_final", 0.9, "PM 正在生成最终报告...")

    from config import MAX_TOKENS_FINAL
    msg = _manager.build_final_message(state)
    messages = [{"role": "user", "content": msg}]
    response = _manager.client.messages.create(
        model=_manager.model,
        max_tokens=MAX_TOKENS_FINAL,
        system=_manager.system_prompt,
        messages=messages,
    )
    text = "".join(b.text for b in response.content if hasattr(b, "text"))

    return {
        "final_report": text,
        "current_node": "manager_final",
        "progress": 1.0,
        "logs": [{"time": time.strftime("%H:%M:%S"), "agent": "manager", "msg": "最终报告生成完毕"}],
    }


# ─────────────── 条件路由 ───────────────

def route_after_review(state: SharedState) -> str:
    if state.get("revision_requests"):
        return "revision_dispatch"
    if state.get("conflicts"):
        return "debater"
    return "stock_advisor"


def revision_dispatch_node(state: SharedState) -> dict:
    """根据 revision_requests 回到对应 Agent"""
    _emit("manager_review", 0.55, "PM 要求专员返工...")
    return {
        "current_node": "revision_dispatch",
        "logs": [{"time": time.strftime("%H:%M:%S"), "agent": "manager",
                  "msg": f"派发返工：{[r['agent'] for r in state.get('revision_requests', [])]}"}],
    }


def route_revision(state: SharedState) -> list[str]:
    """返工路由：返回需要重做的 agent 列表"""
    agents_to_redo = set()
    for rr in state.get("revision_requests", []):
        agent = rr.get("agent", "")
        if agent in ("analyst", "report_reader", "deep_diver", "horizontal_scanner", "tech_scout"):
            agents_to_redo.add(agent)
    return list(agents_to_redo) if agents_to_redo else ["manager_review_post_revision"]


# ─────────────── 构建图 ───────────────

def build_graph() -> Any:
    builder = StateGraph(SharedState)

    # 注册节点
    builder.add_node("manager_plan", manager_plan_node)
    builder.add_node("analyst", analyst_node)
    builder.add_node("report_reader", report_reader_node)
    builder.add_node("deep_diver", deep_diver_node)
    builder.add_node("horizontal_scanner", horizontal_scanner_node)
    builder.add_node("tech_scout", tech_scout_node)
    builder.add_node("manager_review", manager_review_node)
    builder.add_node("revision_dispatch", revision_dispatch_node)
    builder.add_node("debater", debater_node)
    builder.add_node("manager_post_debate", manager_post_debate_node)
    builder.add_node("stock_advisor", stock_advisor_node)
    builder.add_node("manager_final", manager_final_node)

    # START → manager_plan
    builder.add_edge(START, "manager_plan")

    # manager_plan → 5个研究 Agent（并行 fan-out）
    builder.add_edge("manager_plan", "analyst")
    builder.add_edge("manager_plan", "report_reader")
    builder.add_edge("manager_plan", "deep_diver")
    builder.add_edge("manager_plan", "horizontal_scanner")
    builder.add_edge("manager_plan", "tech_scout")

    # 5个 Agent → manager_review（fan-in）
    builder.add_edge("analyst", "manager_review")
    builder.add_edge("report_reader", "manager_review")
    builder.add_edge("deep_diver", "manager_review")
    builder.add_edge("horizontal_scanner", "manager_review")
    builder.add_edge("tech_scout", "manager_review")

    # manager_review → 条件路由
    builder.add_conditional_edges(
        "manager_review",
        route_after_review,
        {
            "revision_dispatch": "revision_dispatch",
            "debater": "debater",
            "stock_advisor": "stock_advisor",
        },
    )

    # 返工 → 回到对应 Agent → 再回 manager_review
    builder.add_conditional_edges(
        "revision_dispatch",
        route_revision,
        {
            "analyst": "analyst",
            "report_reader": "report_reader",
            "deep_diver": "deep_diver",
            "horizontal_scanner": "horizontal_scanner",
            "tech_scout": "tech_scout",
        },
    )

    # 辩论 → PM采纳 → 荐股
    builder.add_edge("debater", "manager_post_debate")
    builder.add_edge("manager_post_debate", "stock_advisor")

    # 荐股 → PM最终报告
    builder.add_edge("stock_advisor", "manager_final")

    # 最终报告 → END
    builder.add_edge("manager_final", END)

    return builder.compile()


def get_initial_state(user_query: str) -> SharedState:
    return SharedState(
        user_query=user_query,
        mece_framework="",
        sub_tasks=[],
        results=[],
        revision_requests=[],
        revision_round=0,
        conflicts=[],
        debate_records=[],
        recommendations=[],
        final_report="",
        current_node="",
        progress=0.0,
        logs=[],
        require_human_review=False,
        error=None,
    )
