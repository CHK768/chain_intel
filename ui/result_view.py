"""
结果展示组件 — Tab 切换显示报告、推荐、MECE、辩论
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTextBrowser, QTableWidget,
    QTableWidgetItem, QHeaderView,
)

from ui.styles import COLORS


class ResultView(QWidget):
    """最终结果展示区，支持多 Tab 切换"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        self._report_view = QTextBrowser()
        self._report_view.setOpenExternalLinks(True)
        self._report_view.setFont(QFont("PingFang SC", 12))
        self._tabs.addTab(self._report_view, "最终报告")

        self._rec_table = QTableWidget()
        self._rec_table.setColumnCount(7)
        self._rec_table.setHorizontalHeaderLabels(
            ["代码", "名称", "评级", "当前价", "目标价", "理由", "风险"]
        )
        self._rec_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tabs.addTab(self._rec_table, "个股推荐")

        self._framework_view = QTextBrowser()
        self._framework_view.setFont(QFont("PingFang SC", 12))
        self._tabs.addTab(self._framework_view, "MECE框架")

        self._debate_view = QTextBrowser()
        self._debate_view.setFont(QFont("PingFang SC", 12))
        self._tabs.addTab(self._debate_view, "辩论记录")

    def set_report(self, markdown_text: str):
        html = self._markdown_to_html(markdown_text)
        self._report_view.setHtml(html)

    def set_framework(self, text: str):
        self._framework_view.setPlainText(text)

    def set_recommendations(self, recs: list[dict]):
        self._rec_table.setRowCount(len(recs))
        for i, rec in enumerate(recs):
            self._rec_table.setItem(i, 0, QTableWidgetItem(rec.get("code", "")))
            self._rec_table.setItem(i, 1, QTableWidgetItem(rec.get("name", "")))
            self._rec_table.setItem(i, 2, QTableWidgetItem(rec.get("rating", "")))
            self._rec_table.setItem(i, 3, QTableWidgetItem(str(rec.get("current_price", ""))))
            target = f"{rec.get('target_price_low', '')}-{rec.get('target_price_high', '')}"
            self._rec_table.setItem(i, 4, QTableWidgetItem(target))
            self._rec_table.setItem(i, 5, QTableWidgetItem(rec.get("rationale", "")[:50]))
            self._rec_table.setItem(i, 6, QTableWidgetItem("; ".join(rec.get("risks", []))))

    def set_debates(self, debates: list[dict]):
        lines = []
        for d in debates:
            lines.append(f"## {d.get('topic', '')}")
            lines.append(f"**正方**: {'; '.join(d.get('pro_arguments', []))}")
            lines.append(f"**反方**: {'; '.join(d.get('con_arguments', []))}")
            lines.append(f"**结论**: {d.get('conclusion', '')}")
            lines.append(f"**置信度**: {d.get('confidence', 0)}")
            lines.append("")
        self._debate_view.setPlainText("\n".join(lines))

    def clear(self):
        self._report_view.clear()
        self._rec_table.setRowCount(0)
        self._framework_view.clear()
        self._debate_view.clear()

    def _markdown_to_html(self, md: str) -> str:
        html = md.replace("\n", "<br>")
        html = f"""<div style="font-family: PingFang SC; font-size: 13px;
                    color: {COLORS['text']}; line-height: 1.6;">
                    {html}</div>"""
        return html
