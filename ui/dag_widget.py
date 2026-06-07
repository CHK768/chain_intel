"""
流程 DAG 可视化组件 — 展示 Agent 节点间的依赖关系和当前执行位置
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPolygonF, QPainterPath,
)
from PyQt6.QtWidgets import QWidget

from ui.styles import COLORS, AGENT_COLORS


# DAG 节点定义：(key, display_name, x, y)  坐标基于归一化网格
DAG_NODES = [
    ("manager_plan", "PM\n框架拆解", 3, 0),
    ("analyst", "数据分析师", 0, 1),
    ("report_reader", "研报研究员", 1.5, 1),
    ("deep_diver", "深挖专员", 3, 1),
    ("horizontal_scanner", "横挖专员", 4.5, 1),
    ("tech_scout", "新技术侦察", 6, 1),
    ("manager_review", "PM\n审核校验", 3, 2),
    ("debater", "辩论协调员", 1.5, 3),
    ("stock_advisor", "荐股分析员", 4.5, 3),
    ("manager_final", "PM\n最终报告", 3, 4),
]

# 边定义：(from_key, to_key)
DAG_EDGES = [
    ("manager_plan", "analyst"),
    ("manager_plan", "report_reader"),
    ("manager_plan", "deep_diver"),
    ("manager_plan", "horizontal_scanner"),
    ("manager_plan", "tech_scout"),
    ("analyst", "manager_review"),
    ("report_reader", "manager_review"),
    ("deep_diver", "manager_review"),
    ("horizontal_scanner", "manager_review"),
    ("tech_scout", "manager_review"),
    ("manager_review", "debater"),
    ("manager_review", "stock_advisor"),
    ("debater", "stock_advisor"),
    ("stock_advisor", "manager_final"),
]


class DagWidget(QWidget):
    """流程 DAG 可视化，显示节点状态和流向箭头"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(260)
        self._node_states: dict[str, str] = {}  # key -> idle/active/done/error
        self._current_node: str = ""

    def set_node_state(self, key: str, state: str):
        self._node_states[key] = state
        self.update()

    def set_current_node(self, key: str):
        self._current_node = key
        self.update()

    def reset(self):
        self._node_states.clear()
        self._current_node = ""
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 计算网格
        margin_x = 50
        margin_y = 25
        grid_w = (w - margin_x * 2) / 6
        grid_h = (h - margin_y * 2) / 4

        def node_center(x, y):
            return QPointF(margin_x + x * grid_w, margin_y + y * grid_h)

        node_positions = {}
        for key, name, gx, gy in DAG_NODES:
            node_positions[key] = node_center(gx, gy)

        # 画边（先画边，再画节点覆盖在上面）
        for from_key, to_key in DAG_EDGES:
            p1 = node_positions[from_key]
            p2 = node_positions[to_key]
            self._draw_edge(painter, p1, p2, from_key, to_key)

        # 画节点
        for key, name, gx, gy in DAG_NODES:
            center = node_positions[key]
            state = self._node_states.get(key, "idle")
            is_current = (key == self._current_node)
            self._draw_node(painter, center, key, name, state, is_current)

        painter.end()

    def _draw_edge(self, painter: QPainter, p1: QPointF, p2: QPointF, from_key: str, to_key: str):
        from_state = self._node_states.get(from_key, "idle")
        to_state = self._node_states.get(to_key, "idle")

        if from_state == "done" and to_state in ("active", "done"):
            color = QColor(COLORS["success"])
            color.setAlpha(200)
            pen_width = 2.0
        elif to_state == "active":
            color = QColor(COLORS["accent"])
            color.setAlpha(180)
            pen_width = 2.0
        else:
            color = QColor(COLORS["border"])
            color.setAlpha(100)
            pen_width = 1.0

        pen = QPen(color, pen_width)
        painter.setPen(pen)

        # 缩短线段，不画进节点内部
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        length = (dx**2 + dy**2) ** 0.5
        if length < 1:
            return
        ux, uy = dx / length, dy / length
        node_r = 24
        start = QPointF(p1.x() + ux * node_r, p1.y() + uy * node_r)
        end = QPointF(p2.x() - ux * node_r, p2.y() - uy * node_r)

        painter.drawLine(start, end)

        # 箭头
        arrow_size = 6
        angle_rad = 0.5  # ~28 degrees
        import math
        ax = end.x() - ux * arrow_size
        ay = end.y() - uy * arrow_size
        lx = ax + arrow_size * (-ux * math.cos(angle_rad) + uy * math.sin(angle_rad))
        ly = ay + arrow_size * (-uy * math.cos(angle_rad) - ux * math.sin(angle_rad))
        rx = ax + arrow_size * (-ux * math.cos(angle_rad) - uy * math.sin(angle_rad))
        ry = ay + arrow_size * (-uy * math.cos(angle_rad) + ux * math.sin(angle_rad))

        arrow = QPolygonF([end, QPointF(lx, ly), QPointF(rx, ry)])
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(arrow)

    def _draw_node(self, painter: QPainter, center: QPointF, key: str, name: str, state: str, is_current: bool):
        r = 22  # 半径

        # 颜色
        agent_color = QColor(AGENT_COLORS.get(key, COLORS["accent"]))

        if state == "active" or is_current:
            fill = QColor(agent_color)
            fill.setAlpha(200)
            border_color = QColor(255, 255, 255, 200)
            text_color = QColor(255, 255, 255)
        elif state == "done":
            fill = QColor(COLORS["success"])
            fill.setAlpha(160)
            border_color = QColor(COLORS["success"])
            text_color = QColor(255, 255, 255)
        elif state == "error":
            fill = QColor(COLORS["error"])
            fill.setAlpha(160)
            border_color = QColor(COLORS["error"])
            text_color = QColor(255, 255, 255)
        else:
            fill = QColor(COLORS["surface"])
            border_color = QColor(COLORS["border"])
            text_color = QColor(COLORS["text_dim"])

        # 当前节点放大光晕
        if is_current:
            glow = QColor(agent_color)
            glow.setAlpha(60)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(center, r + 6, r + 6)

        # 节点圆
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(QBrush(fill))
        painter.drawEllipse(center, r, r)

        # 文字
        painter.setPen(QPen(text_color))
        font = QFont("PingFang SC", 8)
        painter.setFont(font)
        rect = QRectF(center.x() - r, center.y() - r, r * 2, r * 2)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, name)
