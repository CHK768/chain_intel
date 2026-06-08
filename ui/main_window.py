"""
主窗口 — 组合所有 UI 组件，连接 LangGraph 执行线程
"""
from __future__ import annotations

import time
import os
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QScrollArea, QFrame,
    QStatusBar, QMessageBox, QFileDialog,
)

from ui.styles import COLORS, MAIN_STYLESHEET, AGENT_COLORS
from ui.agent_panel import AgentPanel
from ui.progress_bar import PipelineProgressBar
from ui.result_view import ResultView
from ui.log_dialog import AgentLogDialog
from ui.dag_widget import DagWidget
from config import AGENT_NAMES


AGENT_DISPLAY_ORDER = [
    ("manager_plan", "项目经理"),
    ("analyst", "数据分析师"),
    ("report_reader", "研报研究员"),
    ("deep_diver", "深挖专员"),
    ("horizontal_scanner", "横挖专员"),
    ("tech_scout", "新技术侦察"),
    ("debater", "辩论协调员"),
    ("stock_advisor", "荐股分析员"),
    ("gatekeeper", "守门员"),
]


class GraphRunnerThread(QThread):
    """后台线程运行 LangGraph"""
    node_started = pyqtSignal(str)
    node_finished = pyqtSignal(str, str)
    progress_updated = pyqtSignal(float, str)
    log_emitted = pyqtSignal(dict)
    completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, user_query: str, parent=None):
        super().__init__(parent)
        self._query = user_query

    def run(self):
        try:
            import sys
            sys.path.insert(0, ".")
            from graph.workflow import build_graph, get_initial_state, set_progress_callback

            def _on_progress(node, progress, msg):
                self.node_started.emit(node)
                self.progress_updated.emit(progress, msg)

            set_progress_callback(_on_progress)

            graph = build_graph()
            initial_state = get_initial_state(self._query)

            accumulated_state = dict(initial_state)
            for event in graph.stream(initial_state, stream_mode="updates"):
                node_name = list(event.keys())[0]
                node_data = event[node_name]

                if isinstance(node_data, dict):
                    # 累积 state
                    for k, v in node_data.items():
                        if k == "results" and isinstance(v, list):
                            accumulated_state.setdefault("results", []).extend(v)
                        elif k == "logs" and isinstance(v, list):
                            accumulated_state.setdefault("logs", []).extend(v)
                        elif k == "progress":
                            old = accumulated_state.get("progress", 0)
                            accumulated_state[k] = max(old, v)
                        else:
                            accumulated_state[k] = v

                    progress = accumulated_state.get("progress", 0)
                    current = node_data.get("current_node", node_name)
                    self.node_started.emit(current)
                    self.progress_updated.emit(progress, f"{AGENT_NAMES.get(current, current)} 执行中")

                    for log in node_data.get("logs", []):
                        self.log_emitted.emit(log)

                    summary = ""
                    for r in node_data.get("results", []):
                        summary = r.get("summary", "")[:100]
                    self.node_finished.emit(current, summary)

            self.completed.emit(accumulated_state)

        except Exception as e:
            self.error_occurred.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("chain_intel — 产业链投资调研系统")
        self.setMinimumSize(1100, 700)
        self.setStyleSheet(MAIN_STYLESHEET)

        icon_path = os.path.join(os.path.dirname(__file__), "assets", "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._logs: list[dict] = []
        self._agent_logs: dict[str, list[dict]] = {}
        self._final_state: dict = {}
        self._runner: GraphRunnerThread | None = None

        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 12, 16, 8)
        main_layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("chain_intel")
        title.setFont(QFont("PingFang SC", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['accent']};")
        header_layout.addWidget(title)

        subtitle = QLabel("产业链投资调研系统")
        subtitle.setFont(QFont("PingFang SC", 13))
        subtitle.setStyleSheet(f"color: {COLORS['text_dim']};")
        header_layout.addWidget(subtitle)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Input area
        input_layout = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("输入研究问题，如：分析半导体产业链投资机会...")
        self._input.setFont(QFont("PingFang SC", 13))
        self._input.returnPressed.connect(self._start_research)
        input_layout.addWidget(self._input, 1)

        self._start_btn = QPushButton("开始调研")
        self._start_btn.setFont(QFont("PingFang SC", 13, QFont.Weight.Bold))
        self._start_btn.clicked.connect(self._start_research)
        input_layout.addWidget(self._start_btn)

        self._export_btn = QPushButton("导出报告")
        self._export_btn.setFont(QFont("PingFang SC", 13))
        self._export_btn.setEnabled(False)
        self._export_btn.clicked.connect(self._export_report)
        input_layout.addWidget(self._export_btn)
        main_layout.addLayout(input_layout)

        # Main content: DAG (top) + agent panel (left) + result (right)
        # DAG flow visualization
        self._dag = DagWidget()
        main_layout.addWidget(self._dag)

        content_layout = QHBoxLayout()

        # Left: Agent panels
        left_frame = QFrame()
        left_frame.setFixedWidth(240)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        self._agent_panels: dict[str, AgentPanel] = {}
        for key, name in AGENT_DISPLAY_ORDER:
            panel = AgentPanel(key, name)
            panel.clicked.connect(self._on_agent_clicked)
            self._agent_panels[key] = panel
            left_layout.addWidget(panel)

        left_layout.addStretch()
        content_layout.addWidget(left_frame)

        # Right: Result view
        self._result_view = ResultView()
        content_layout.addWidget(self._result_view, 1)
        main_layout.addLayout(content_layout, 1)

        # Progress bar
        self._progress = PipelineProgressBar()
        main_layout.addWidget(self._progress)

        # Status bar
        self._statusbar = QStatusBar()
        self._statusbar.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px;")
        self.setStatusBar(self._statusbar)
        self._statusbar.showMessage("就绪")

    def _start_research(self):
        query = self._input.text().strip()
        if not query:
            return

        self._start_btn.setEnabled(False)
        self._result_view.clear()
        self._progress.reset()
        self._dag.reset()
        self._logs.clear()
        self._agent_logs.clear()
        self._final_state.clear()
        self._current_progress = 0.0

        for panel in self._agent_panels.values():
            panel.set_state("idle")
            panel.set_preview("")

        self._statusbar.showMessage("调研进行中...")
        self._start_time = time.time()

        self._runner = GraphRunnerThread(query)
        self._runner.node_started.connect(self._on_node_started)
        self._runner.node_finished.connect(self._on_node_finished)
        self._runner.progress_updated.connect(self._on_progress)
        self._runner.log_emitted.connect(self._on_log)
        self._runner.completed.connect(self._on_completed)
        self._runner.error_occurred.connect(self._on_error)
        self._runner.start()

    def _on_node_started(self, node: str):
        if node in self._agent_panels:
            self._agent_panels[node].set_state("active")
        for key in ("manager_review", "manager_post_debate", "manager_final"):
            if node == key and "manager_plan" in self._agent_panels:
                self._agent_panels["manager_plan"].set_state("active")
        self._dag.set_node_state(node, "active")
        self._dag.set_current_node(node)

    def _on_node_finished(self, node: str, summary: str):
        if node in self._agent_panels:
            self._agent_panels[node].set_state("done")
            if summary:
                self._agent_panels[node].set_preview(summary)
        for key in ("manager_review", "manager_post_debate", "manager_final"):
            if node == key and "manager_plan" in self._agent_panels:
                self._agent_panels["manager_plan"].set_state("done")
        self._dag.set_node_state(node, "done")

    def _on_progress(self, value: float, msg: str):
        if value > self._current_progress:
            self._current_progress = value
            self._progress.set_progress(value, msg)

    def _on_log(self, log: dict):
        self._logs.append(log)
        agent = log.get("agent", "unknown")
        if agent not in self._agent_logs:
            self._agent_logs[agent] = []
        self._agent_logs[agent].append(log)

    def _on_completed(self, state: dict):
        self._final_state = state
        self._start_btn.setEnabled(True)
        self._export_btn.setEnabled(True)

        elapsed = time.time() - self._start_time
        self._statusbar.showMessage(f"调研完成 | 耗时 {elapsed:.1f}s")
        self._progress.set_progress(1.0, "完成")

        for panel in self._agent_panels.values():
            panel.set_state("done")

        if state.get("final_report"):
            self._result_view.set_report(state["final_report"])
        if state.get("mece_framework"):
            self._result_view.set_framework(state["mece_framework"])
        if state.get("recommendations"):
            self._result_view.set_recommendations(state["recommendations"])
        if state.get("debate_records"):
            self._result_view.set_debates(state["debate_records"])

    def _on_error(self, error: str):
        self._start_btn.setEnabled(True)
        self._statusbar.showMessage(f"错误: {error[:80]}")
        self._progress.set_progress(0, "出错")
        QMessageBox.critical(self, "执行错误", error)

    def _on_agent_clicked(self, agent_key: str):
        agent_name = AGENT_NAMES.get(agent_key, agent_key)
        logs = self._agent_logs.get(agent_key, [])
        if agent_key.startswith("manager"):
            logs = self._agent_logs.get("manager", [])
        dialog = AgentLogDialog(agent_name, logs, self)
        dialog.exec()

    def _export_report(self):
        if not self._final_state:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "导出报告", "chain_intel_report.html",
            "HTML文件 (*.html);;Markdown文件 (*.md)"
        )
        if not path:
            return

        state = self._final_state
        if path.endswith(".md"):
            content = self._build_markdown_report(state)
        else:
            content = self._build_html_report(state)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        self._statusbar.showMessage(f"报告已导出: {path}")

    def _build_markdown_report(self, state: dict) -> str:
        lines = []
        lines.append(f"# 投资调研报告\n")
        lines.append(f"**研究问题**: {state.get('user_query', '')}\n")
        lines.append(f"---\n")

        if state.get("mece_framework"):
            lines.append(f"## MECE 分析框架\n")
            lines.append(state["mece_framework"])
            lines.append("\n")

        if state.get("final_report"):
            lines.append(f"## 详细报告\n")
            lines.append(state["final_report"])
            lines.append("\n")

        if state.get("recommendations"):
            lines.append(f"## 个股推荐\n")
            lines.append("| 代码 | 名称 | 评级 | 当前价 | 目标价 | 理由 |")
            lines.append("|------|------|------|--------|--------|------|")
            for rec in state["recommendations"]:
                target = f"{rec.get('target_price_low', '?')}-{rec.get('target_price_high', '?')}"
                lines.append(f"| {rec.get('code','')} | {rec.get('name','')} | {rec.get('rating','')} | {rec.get('current_price','')} | {target} | {rec.get('rationale','')} |")
            lines.append("\n")

        if state.get("debate_records"):
            lines.append(f"## 辩论记录\n")
            for d in state["debate_records"]:
                lines.append(f"### {d.get('topic', '')}")
                lines.append(f"**正方**: {'; '.join(d.get('pro_arguments', []))}")
                lines.append(f"**反方**: {'; '.join(d.get('con_arguments', []))}")
                lines.append(f"**结论**: {d.get('conclusion', '')}")
                lines.append(f"**置信度**: {d.get('confidence', 0)}\n")

        if state.get("results"):
            lines.append(f"## 各专员研究详情\n")
            for r in state["results"]:
                lines.append(f"### {r.get('agent', '')}")
                lines.append(r.get("details", r.get("summary", "")))
                lines.append("\n")

        return "\n".join(lines)

    def _build_html_report(self, state: dict) -> str:
        md = self._build_markdown_report(state)
        # 简单转 HTML
        body = md.replace("\n", "<br>\n")
        return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>chain_intel 投资调研报告</title>
<style>
body {{ font-family: 'PingFang SC', sans-serif; max-width: 900px; margin: 40px auto;
       padding: 20px; line-height: 1.8; color: #333; }}
h1 {{ color: #7c8aff; border-bottom: 2px solid #7c8aff; padding-bottom: 8px; }}
h2 {{ color: #4a4a6a; margin-top: 30px; }}
h3 {{ color: #666; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background: #f5f5ff; }}
strong {{ color: #4a4a6a; }}
</style>
</head><body>
{body}
</body></html>"""
