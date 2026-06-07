"""
Agent 日志查看弹窗
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QLineEdit,
)

from ui.styles import COLORS, MAIN_STYLESHEET


class AgentLogDialog(QDialog):
    """查看某 Agent 的详细执行日志"""

    def __init__(self, agent_name: str, logs: list[dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{agent_name} - 执行日志")
        self.setMinimumSize(600, 400)
        self.setStyleSheet(MAIN_STYLESHEET)

        layout = QVBoxLayout(self)

        header = QLabel(f"{agent_name} 执行记录")
        header.setFont(QFont("PingFang SC", 14, QFont.Weight.Bold))
        layout.addWidget(header)

        search_layout = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索日志...")
        self._search.textChanged.connect(self._filter_logs)
        search_layout.addWidget(self._search)
        layout.addLayout(search_layout)

        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setFont(QFont("Menlo", 11))
        layout.addWidget(self._text)

        self._logs = logs
        self._render_logs(logs)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _render_logs(self, logs: list[dict]):
        lines = []
        for log in logs:
            t = log.get("time", "")
            agent = log.get("agent", "")
            msg = log.get("msg", "")
            lines.append(f"[{t}] [{agent}] {msg}")
        self._text.setPlainText("\n".join(lines))

    def _filter_logs(self, text: str):
        if not text:
            self._render_logs(self._logs)
            return
        filtered = [l for l in self._logs if text.lower() in str(l).lower()]
        self._render_logs(filtered)
