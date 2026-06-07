"""
BaseAgent — 所有角色的基类，封装 Claude API 交互
"""
from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from typing import Any

from anthropic import Anthropic

from config import ANTHROPIC_API_KEY, AGENT_MODEL, MAX_TOKENS_AGENT


class BaseAgent(ABC):
    name: str = ""
    role: str = ""
    system_prompt: str = ""

    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = AGENT_MODEL
        self.max_tokens = MAX_TOKENS_AGENT

    @abstractmethod
    def get_tools(self) -> list[dict]:
        """返回该 Agent 可用的 tool 定义列表（Anthropic tool_use 格式）"""
        return []

    @abstractmethod
    def build_user_message(self, state: dict) -> str:
        """根据当前 state 构建 user message"""
        ...

    def execute(self, state: dict) -> dict:
        """
        调用 Claude API 执行任务，处理 tool_use 循环，返回结果。
        采用循环检测而非硬性次数限制：连续相同调用视为死循环。
        """
        messages = [{"role": "user", "content": self.build_user_message(state)}]
        tools = self.get_tools()

        all_tool_outputs = []
        recent_calls = []  # 记录最近的工具调用签名，用于检测循环
        MAX_REPEAT = 3     # 连续N次相同调用判定为死循环

        while True:
            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "system": self.system_prompt,
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = tools

            response = self.client.messages.create(**kwargs)

            if response.stop_reason == "tool_use":
                tool_results = []
                assistant_content = response.content
                for block in assistant_content:
                    if block.type == "tool_use":
                        call_sig = f"{block.name}:{json.dumps(block.input, sort_keys=True)}"
                        recent_calls.append(call_sig)

                        # 循环检测：最近 MAX_REPEAT 次调用完全相同
                        if len(recent_calls) >= MAX_REPEAT:
                            tail = recent_calls[-MAX_REPEAT:]
                            if len(set(tail)) == 1:
                                return self._fallback_response(all_tool_outputs)

                        result = self._handle_tool_call(block.name, block.input)
                        all_tool_outputs.append({
                            "tool": block.name,
                            "input": block.input,
                            "output": result,
                        })
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result, ensure_ascii=False, default=str)[:4000],
                        })
                messages.append({"role": "assistant", "content": assistant_content})
                messages.append({"role": "user", "content": tool_results})
            else:
                text = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        text += block.text
                return self._parse_response(text, all_tool_outputs)

    def _fallback_response(self, tool_outputs: list) -> dict:
        """循环检测触发时，用已有中间结果生成保底输出"""
        summary_parts = []
        for to in tool_outputs:
            out = to.get("output", {})
            if isinstance(out, list) and out:
                summary_parts.append(f"[{to['tool']}] 返回 {len(out)} 条结果")
            elif isinstance(out, dict) and "error" not in out:
                summary_parts.append(f"[{to['tool']}] {json.dumps(out, ensure_ascii=False)[:100]}")
        summary = "（循环检测中断）已获取的中间结果：\n" + "\n".join(summary_parts) if summary_parts else "（循环检测中断，无有效结果）"
        return self._parse_response(summary, tool_outputs)

    def _handle_tool_call(self, tool_name: str, tool_input: dict) -> Any:
        """分发工具调用到具体实现，子类可覆盖"""
        handler = self.get_tool_handlers().get(tool_name)
        if handler:
            try:
                return handler(**tool_input)
            except Exception as e:
                return {"error": str(e)}
        return {"error": f"Unknown tool: {tool_name}"}

    def get_tool_handlers(self) -> dict:
        """返回 {tool_name: callable} 映射，子类实现"""
        return {}

    def _parse_response(self, text: str, tool_outputs: list) -> dict:
        """解析最终文本响应为结构化输出"""
        evidences = []
        for to in tool_outputs:
            evidences.append({
                "source": to["tool"],
                "url": None,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "confidence": 0.8,
                "content": json.dumps(to["input"], ensure_ascii=False)[:200],
            })
        return {
            "summary": text[:500] if text else "",
            "details": text,
            "evidences": evidences,
        }
