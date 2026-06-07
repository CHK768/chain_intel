"""
流水线进度条组件
"""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar

from ui.styles import COLORS


class PipelineProgressBar(QWidget):
    """整体进度条 + 当前阶段描述"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(4)

        top_layout = QHBoxLayout()
        self._stage_label = QLabel("就绪")
        self._stage_label.setFont(QFont("PingFang SC", 11))
        top_layout.addWidget(self._stage_label)

        top_layout.addStretch()

        self._pct_label = QLabel("0%")
        self._pct_label.setFont(QFont("PingFang SC", 11, QFont.Weight.Bold))
        self._pct_label.setStyleSheet(f"color: {COLORS['accent']};")
        top_layout.addWidget(self._pct_label)

        layout.addLayout(top_layout)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        layout.addWidget(self._bar)

    def set_progress(self, value: float, stage_text: str = ""):
        pct = int(value * 100)
        self._bar.setValue(pct)
        self._pct_label.setText(f"{pct}%")
        if stage_text:
            self._stage_label.setText(stage_text)

    def reset(self):
        self._bar.setValue(0)
        self._pct_label.setText("0%")
        self._stage_label.setText("就绪")
