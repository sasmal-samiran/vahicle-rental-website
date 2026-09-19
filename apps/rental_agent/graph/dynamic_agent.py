import json
import time
from typing import Any, AsyncGenerator, Sequence


class DynamicRentalAgent:
    async def execute_task(
        self,
        agent: Any,
        messages: Sequence[Any],
        model_name: str = "default",
    ) -> AsyncGenerator[dict[str, Any], None]:
        started_at = time.time()
        first_token_at = None
        tool_start_times: dict[str, float] = {}

        try:
            async for event in agent.astream_events(
                {"messages": list(messages)},
                version="v2",
            ):
                event_name = event.get("event")
                now = time.time()
                elapsed = max(0.01, round(now - started_at, 2))

                if event_name == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    tool_start_times[tool_name] = now
                    yield {
                        "type": "tool_start",
                        "tool": tool_name,
                        "input": event.get("data", {}).get("input", {}),
                        "message": f"Executing {tool_name}...",
                        "description": f"Executed {tool_name} on host webpage.",
                        "duration": None,
                        "elapsed": elapsed,
                        "timestamp": now,
                    }

                elif event_name == "on_tool_end":
                    tool_name = event.get("name", "unknown")
                    start = tool_start_times.pop(tool_name, now)
                    output = event.get("data", {}).get("output", "")
                    content = getattr(output, "content", output)
                    output_text = content if isinstance(content, str) else json.dumps(content, default=str)
                    yield {
                        "type": "tool_end",
                        "tool": tool_name,
                        "output": output_text or "Tool completed without output.",
                        "duration": max(0.01, round(now - start, 2)),
                        "elapsed": elapsed,
                        "message": f"Completed {tool_name}",
                        "timestamp": now,
                    }

                elif event_name == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    content = getattr(chunk, "content", None) if chunk else None
                    token_texts = [content] if isinstance(content, str) else []
                    if isinstance(content, list):
                        token_texts = [
                            block if isinstance(block, str) else block.get("text", "")
                            for block in content
                            if isinstance(block, str) or isinstance(block, dict)
                        ]

                    for token_text in token_texts:
                        if not token_text:
                            continue
                        token_event = {
                            "type": "token",
                            "content": token_text,
                            "model": model_name,
                            "elapsed": elapsed,
                        }
                        if first_token_at is None:
                            first_token_at = now
                            token_event["thought_duration"] = max(
                                0.05, round(now - started_at, 2)
                            )
                        yield token_event

            finished_at = time.time()
            total_duration = max(0.01, round(finished_at - started_at, 2))
            yield {
                "type": "done",
                "model": model_name,
                "thought_duration": max(
                    0.05,
                    round((first_token_at or finished_at) - started_at, 2),
                ),
                "total_duration": total_duration,
                "duration": total_duration,
                "timestamp": finished_at,
            }
        except Exception as exc:
            now = time.time()
            yield {
                "type": "error",
                "error_code": getattr(exc, "status_code", None) or 500,
                "message": "The assistant encountered an issue processing your request. Please try again.",
                "duration": max(0.01, round(now - started_at, 2)),
                "retryable": True,
                "timestamp": now,
            }


dynamic_agent = DynamicRentalAgent()
