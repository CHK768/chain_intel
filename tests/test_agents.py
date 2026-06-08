"""
Agent 角色单元测试 — 验证每个角色可正常实例化、schema 正确、API 连通
"""
from __future__ import annotations

import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault("DEEPSEEK_API_KEY", "sk-63ef2f23caac402f871c7b54a657f10e")
os.environ.setdefault("TUSHARE_TOKEN", "9f4c59a4ae23ffc41288c4bf0c52e7df8502208667fb2c0562c0e993")

from agents.manager import ManagerAgent
from agents.analyst import AnalystAgent
from agents.report_reader import ReportReaderAgent
from agents.deep_diver import DeepDiverAgent
from agents.horizontal_scanner import HorizontalScannerAgent
from agents.tech_scout import TechScoutAgent
from agents.debater import DebaterAgent
from agents.stock_advisor import StockAdvisorAgent

PASS = "✅"
FAIL = "❌"
WARN = "⚠️"


def check_tool_schemas(agent) -> tuple[bool, str]:
    tools = agent.get_tools()
    if not tools:
        return True, "无工具（纯文本）"
    issues = []
    for i, tool in enumerate(tools):
        if "name" not in tool:
            issues.append(f"tool[{i}] 缺少 name")
        if "description" not in tool:
            issues.append(f"tool[{i}] 缺少 description")
        schema = tool.get("input_schema", {})
        if schema.get("type") != "object":
            issues.append(f"tool[{i}] input_schema.type 不是 object")
        if "properties" not in schema:
            issues.append(f"tool[{i}] input_schema 缺少 properties")
    if issues:
        return False, "; ".join(issues)
    return True, "OK"


def check_tool_handlers(agent) -> tuple[bool, str]:
    tools = agent.get_tools()
    handlers = agent.get_tool_handlers()
    tool_names = {t["name"] for t in tools}
    handler_names = set(handlers.keys())
    missing = tool_names - handler_names
    if missing:
        return False, f"缺少 handler: {missing}"
    extra = handler_names - tool_names
    if extra:
        return False, f"多余的 handler: {extra}"
    return True, "OK"


def build_state_with_rich_context(agent_name: str) -> dict:
    """构建包含丰富前置数据的完整 state，让所有 agent 都能正常工作"""
    task_for_agent = {
        "manager": "测试任务：简要分析半导体产业链投资机会，输出3个关键发现。",
        "analyst": "测试任务：简要分析半导体板块近期A股数据，输出3个关键发现。",
        "report_reader": "测试任务：简要概述半导体行业最新券商观点，输出3个关键发现。",
        "deep_diver": "测试任务：简要分析半导体上游设备材料的国产替代进展，输出3个关键发现。",
        "horizontal_scanner": "测试任务：简要对比半导体设计环节的竞争格局，输出3个关键发现。",
        "tech_scout": "测试任务：简要介绍半导体领域的前沿技术趋势，输出3个关键发现。",
        "debater": "不需要额外任务——辩论协调员由冲突触发。",
        "stock_advisor": "测试任务：基于研究结论筛选3-5个A股半导体标的并给出评级。",
    }

    # 为 stock_advisor 准备包含充分研究数据的 state
    return {
        "user_query": "分析2025年半导体产业链投资机会",
        "mece_framework": "1. 上游设备材料\n2. 中游芯片设计与制造\n3. 下游封测与应用\n4. 新技术趋势\n5. 竞争格局",
        "sub_tasks": [
            {"agent": agent_name, "task": task_for_agent.get(agent_name, "简要分析半导体产业链")}
        ],
        "results": [
            {
                "agent": "analyst",
                "summary": "A股半导体板块估值处于历史中位数下方，设备龙头北方华创、中微公司营收增速超30%。"
                         "封测环节长电科技、通富微电业绩改善明显。主力资金近一月净流入半导体设备板块超80亿。",
                "details": "详细数据分析：半导体设备国产化率从2020年15%提升至2025年约35%。"
                          "北方华创2025Q1营收同比+42%，订单饱满。中微公司刻蚀机突破5nm节点。"
                          "封测环节受AI芯片需求拉动，先进封装(Chiplet)成为新增长极。"
            },
            {
                "agent": "report_reader",
                "summary": "中信证券、华泰证券等多家头部券商维持半导体板块'强于大市'评级。"
                         "WSTS预计2025年全球半导体市场规模达6971亿美元，同比+12.5%。"
                         "关注AI芯片、先进封装、半导体设备三条主线。",
                "details": "券商共识：半导体周期2024Q4确认底部，2025年温和复苏。分歧点在于复苏斜率——"
                          "乐观派认为AI驱动超预期增长，谨慎派认为消费电子需求复苏乏力。"
            },
            {
                "agent": "deep_diver",
                "summary": "半导体产业链上游分为：硅片(沪硅产业)、光刻胶(彤程新材)、电子特气(华特气体)、"
                         "溅射靶材(江丰电子)、CMP抛光液(安集科技)。国产替代核心环节为光刻机>检测设备>光刻胶。",
                "details": "供应链深度分析：①硅片——沪硅产业12英寸硅片已通过中芯国际验证，良率80%+；"
                          "②光刻胶——ArF光刻胶国内彤程新材、上海新阳小批量供货，但高端EUV仍被TOK/JSR垄断；"
                          "③设备零部件——国产化率仍低于20%，富创精密、新莱应材有突破。"
            },
            {
                "agent": "horizontal_scanner",
                "summary": "半导体设计环节竞争格局：CIS——韦尔股份(全球第三) vs 格科微(中低端)；"
                         "MCU——兆易创新 vs 中颖电子 vs 国民技术；存储——兆易创新 vs 北京君正 vs 普冉股份。"
                         "整体格局：高端市场仍由海外主导，中低端国产替代加速。",
            },
            {
                "agent": "tech_scout",
                "summary": "前沿趋势：①Chiplet先进封装——通富微电、长电科技已布局；②第三代半导体SiC——"
                         "天岳先进、天科合达衬底突破；③Chiplet互联标准UCIe——中国厂商积极参与；"
                         "④AI芯片定制化ASIC——寒武纪、海光信息受益。",
            },
        ],
        "revision_requests": [],
        "revision_round": 0,
        "conflicts": [],
        "debate_records": [],
        "recommendations": [],
        "logs": [],
    }


def main():
    print("=" * 70)
    print("chain_intel Agent 角色全面测试")
    print("=" * 70)

    agents_to_test = [
        (ManagerAgent, "manager", "项目经理"),
        (AnalystAgent, "analyst", "数据分析师"),
        (ReportReaderAgent, "report_reader", "研报研究员"),
        (DeepDiverAgent, "deep_diver", "深挖专员"),
        (HorizontalScannerAgent, "horizontal_scanner", "横挖专员"),
        (TechScoutAgent, "tech_scout", "新技术侦察员"),
        (DebaterAgent, "debater", "辩论协调员"),
        (StockAdvisorAgent, "stock_advisor", "荐股分析员"),
    ]

    all_pass = True
    living_agents = {}

    for agent_class, key, display_name in agents_to_test:
        print(f"\n{'─' * 70}")
        print(f"  {display_name} ({key})")
        print(f"{'─' * 70}")

        agent = None
        # 1. 实例化
        try:
            agent = agent_class()
            living_agents[key] = agent
            print(f"  {PASS} 实例化")
        except Exception as e:
            print(f"  {FAIL} 实例化 — {e}")
            all_pass = False
            continue

        # 2. 属性检查
        try:
            assert agent.name, "name 为空"
            assert agent.role, "role 为空"
            assert agent.system_prompt, "system_prompt 为空"
            assert agent.model, "model 为空"
            assert agent.client, "client 未创建"
            print(f"  {PASS} 属性 (name={agent.name}, model={agent.model})")
        except Exception as e:
            print(f"  {FAIL} 属性 — {e}")
            all_pass = False

        # 3. Tool schema
        ok, detail = check_tool_schemas(agent)
        print(f"  {PASS if ok else FAIL} Tool schema ({len(agent.get_tools())}个)" + (f" — {detail}" if not ok else ""))

        # 4. Tool handlers
        ok, detail = check_tool_handlers(agent)
        print(f"  {PASS if ok else FAIL} Tool handlers" + (f" — {detail}" if not ok else ""))

        # 5. build_user_message（ManagerAgent 特例：返回空字符串是预期行为）
        try:
            msg = agent.build_user_message(build_state_with_rich_context(key))
            if isinstance(msg, str):
                if key == "manager" and msg == "":
                    print(f"  {PASS} build_user_message (manager 专用方法：plan/review/final)")
                elif len(msg) > 10:
                    print(f"  {PASS} build_user_message (长度={len(msg)})")
                else:
                    print(f"  {WARN} build_user_message — 输出较短: {msg[:80]}")
            else:
                print(f"  {FAIL} build_user_message — 非 str 类型: {type(msg)}")
                all_pass = False
        except Exception as e:
            print(f"  {FAIL} build_user_message — {e}")
            all_pass = False

    # ── API 连通测试 ──
    print(f"\n{'=' * 70}")
    print("  DeepSeek API 连通性测试")
    print(f"{'=' * 70}")

    for agent_class, key, display_name in agents_to_test:
        agent = living_agents.get(key)
        if agent is None:
            print(f"  {FAIL} {display_name}: 实例化失败，跳过")
            all_pass = False
            continue

        state = build_state_with_rich_context(key)
        print(f"\n  ▶ {display_name} ({key}) — {agent.model}")

        try:
            start = __import__('time').time()
            result = agent.execute(state)
            elapsed = __import__('time').time() - start

            summary = result.get("summary", "")
            details = result.get("details", "")
            evidence_count = len(result.get("evidences", []))

            if summary and len(summary) > 20:
                print(f"    {PASS} API — {len(details)}字, {evidence_count}条证据, {elapsed:.1f}s")
            elif summary:
                print(f"    {WARN} API — summary较短({len(summary)}字), {elapsed:.1f}s")
            else:
                print(f"    {FAIL} API — summary 为空, {elapsed:.1f}s")
                print(f"    details前100字: {details[:100]}")
                all_pass = False
        except Exception as e:
            tb = traceback.format_exc()
            print(f"    {FAIL} API — {e}")
            print(f"    {tb[-400:]}")
            all_pass = False

    # ── 汇总 ──
    print(f"\n{'=' * 70}")
    if all_pass:
        print(f"  {PASS} 所有角色测试通过")
    else:
        print(f"  {FAIL} 存在失败项")
    print(f"{'=' * 70}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
