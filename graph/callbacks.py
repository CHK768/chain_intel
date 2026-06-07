"""
进度回调 — 连接 LangGraph 执行与 UI 信号
"""
from __future__ import annotations

from typing import Callable, Optional


class ProgressTracker:
    """跟踪图执行进度，转发给 UI"""

    def __init__(self):
        self._on_node_start: Optional[Callable] = None
        self._on_progress: Optional[Callable] = None
        self._on_log: Optional[Callable] = None

    def set_callbacks(
        self,
        on_node_start: Optional[Callable] = None,
        on_progress: Optional[Callable] = None,
        on_log: Optional[Callable] = None,
    ):
        self._on_node_start = on_node_start
        self._on_progress = on_progress
        self._on_log = on_log

    def notify(self, node: str, progress: float, msg: str = ""):
        if self._on_node_start:
            self._on_node_start(node)
        if self._on_progress:
            self._on_progress(progress, msg)
        if self._on_log and msg:
            self._on_log(node, "info", msg)


tracker = ProgressTracker()
