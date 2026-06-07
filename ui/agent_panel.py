"""
角色面板组件 — 展示 Agent 头像、状态、日志预览
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPixmap
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget

import os
from ui.styles import AGENT_COLORS, COLORS


class StatusIndicator(QWidget):
    """圆形状态指示灯，支持脉冲动画"""

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self._color = QColor(color)
        self._opacity = 1.0
        self._state = "idle"
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse_tick)
        self._pulse_dir = -1

    def set_state(self, state: str):
        self._state = state
        if state == "active":
            self._pulse_timer.start(50)
        else:
            self._pulse_timer.stop()
            self._opacity = 1.0
        self.update()

    def _pulse_tick(self):
        self._opacity += self._pulse_dir * 0.04
        if self._opacity <= 0.3:
            self._pulse_dir = 1
        elif self._opacity >= 1.0:
            self._pulse_dir = -1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._state == "idle":
            color = QColor(COLORS["border"])
        elif self._state == "active":
            color = QColor(self._color)
            color.setAlphaF(self._opacity)
        elif self._state == "done":
            color = QColor(COLORS["success"])
        elif self._state == "error":
            color = QColor(COLORS["error"])
        else:
            color = QColor(COLORS["border"])

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawEllipse(1, 1, 10, 10)
        painter.end()


class AgentPanel(QFrame):
    """单个 Agent 的状态面板"""
    clicked = pyqtSignal(str)

    def __init__(self, agent_key: str, display_name: str, parent=None):
        super().__init__(parent)
        self._agent_key = agent_key
        self._display_name = display_name
        self._state = "idle"
        self._color = AGENT_COLORS.get(agent_key, COLORS["accent"])

        self.setFixedHeight(52)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()
        self._update_style()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Avatar
        avatar_path = os.path.join(os.path.dirname(__file__), "assets", f"{self._agent_key}.png")
        self._avatar_label = QLabel()
        self._avatar_label.setFixedSize(36, 36)
        if os.path.exists(avatar_path):
            pixmap = QPixmap(avatar_path).scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
            self._avatar_label.setPixmap(pixmap)
        else:
            self._avatar_label.setStyleSheet(f"background-color: {self._color}; border-radius: 18px;")
        layout.addWidget(self._avatar_label)

        self._indicator = StatusIndicator(self._color, self)
        layout.addWidget(self._indicator)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(0)

        self._name_label = QLabel(self._display_name)
        self._name_label.setFont(QFont("PingFang SC", 12, QFont.Weight.Bold))
        info_layout.addWidget(self._name_label)

        self._preview_label = QLabel("")
        self._preview_label.setFont(QFont("PingFang SC", 10))
        self._preview_label.setStyleSheet(f"color: {COLORS['text_dim']};")
        self._preview_label.setMaximumWidth(200)
        info_layout.addWidget(self._preview_label)

        layout.addLayout(info_layout, 1)

    def _update_style(self):
        if self._state == "active":
            border_color = self._color
            bg = COLORS["surface_hover"]
        elif self._state == "done":
            border_color = COLORS["success"]
            bg = COLORS["surface"]
        elif self._state == "error":
            border_color = COLORS["error"]
            bg = COLORS["surface"]
        else:
            border_color = COLORS["border"]
            bg = COLORS["surface"]

        self.setStyleSheet(f"""
            AgentPanel {{
                background-color: {bg};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
        """)

    def set_state(self, state: str):
        self._state = state
        self._indicator.set_state(state)
        self._update_style()

    def set_preview(self, text: str):
        truncated = text[:40] + "..." if len(text) > 40 else text
        self._preview_label.setText(truncated)

    def mousePressEvent(self, event):
        self.clicked.emit(self._agent_key)
        super().mousePressEvent(event)
