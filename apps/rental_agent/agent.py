import time, json
from typing import Optional, List, Dict, Any
from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
)

from .graph.graph import RentalGraph
from .graph.router import classify_intent
from .tools import get_private_tools, get_public_tools
from .llm.models import get_llm
from .llm.prompts import SYSTEM_PROMPT
from .settings import settings
from utils.logger import get_logger

logger = get_logger("rental_agent")

MAX_TOOL_OUTPUT_CHARS = 4000
MAX_HISTORY_CHARS = 12000


def get_memory(history: Optional[List[Dict[str, Any]]] = None) -> List[BaseMessage]:
    messages: List[BaseMessage] = []
    history_chars = 0
    for item in (history or [])[-5:]:
        if not isinstance(item, dict):
            continue
        text = item.get("text") or item.get("content") or ""
        sender = item.get("sender") or item.get("role")
        if sender in ("user", "human"):
            if text:
                messages.append(HumanMessage(content=text))
        elif sender in ("assistant", "ai", "bot"):
            tool_outputs = []
            for step in item.get("toolSteps", []):
                if not isinstance(step, dict):
                    continue
                output = step.get("output")
                if output:
                    output = str(output)[:MAX_TOOL_OUTPUT_CHARS]
                    tool_outputs.append(
                        f"{step.get('tool', 'tool')} result: {output}"
                    )

            if tool_outputs:
                text = "\n\n".join(filter(None, [text, *tool_outputs]))
            if text:
                remaining_chars = MAX_HISTORY_CHARS - history_chars
                if remaining_chars <= 0:
                    continue
                text = text[:remaining_chars]
                messages.append(AIMessage(content=text))
                history_chars += len(text)

    return messages

def is_rate_limit_error(exc: Exception) -> bool:
    """Check if the given exception is a 429 Too Many Requests / Rate Limit Error from the LLM provider."""
    if exc is None:
        return False

    # Check status_code or code attributes
    status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if status_code == 429:
        return True

    # Check response attribute if attached
    resp = getattr(exc, "response", None)
    if resp is not None:
        resp_status = getattr(resp, "status_code", None)
        if resp_status == 429:
            return True

    # Check error message strings for rate limit patterns
    err_str = str(exc).lower()
    rate_limit_patterns = [
        "429",
        "rate limit",
        "ratelimit",
        "rate_limit_exceeded",
        "too many requests",
        "tokens per minute",
        "requests per minute",
        "tpm",
        "rpm",
        "quota exceeded",
        "resource has been exhausted",
        "insufficient_quota"
    ]
    return any(p in err_str for p in rate_limit_patterns)


def is_request_too_large_error(exc: Exception) -> bool:
    if exc is None:
        return False

    status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if status_code == 413:
        return True

    response = getattr(exc, "response", None)
    if response is not None and getattr(response, "status_code", None) == 413:
        return True

    error_text = str(exc).lower()
    return "request entity too large" in error_text or "payload too large" in error_text

class RentalAgent:
    def __init__(self):
        self.current_model_index: int = 0

    async def execute_task(
        self,
        user,
        message,
        history,
        last_model=None
    ):        
        total_models = len(settings.MODELS)
        if total_models == 0:
            yield {
                "type": "error",
                "error_code": 500,
                "message": "No AI models configured.",
                "duration": 0.0,
                "retryable": False,
                "timestamp": time.time()
            }
            return
        
        # 1. Resolve starting model (explicit last_model > last model in history > current instance index)
        start_index = self.current_model_index % total_models
        if last_model and last_model in settings.MODELS:
            start_index = settings.MODELS.index(last_model)
        elif history:
            for item in reversed(history):
                if isinstance(item, dict) and item.get("model"):
                    hist_model = item.get("model")
                    if hist_model in settings.MODELS:
                        start_index = settings.MODELS.index(hist_model)
                        break

        # 2. Cycle through all available models in round-robin fashion
        for attempt in range(total_models):
            idx = (start_index + attempt) % total_models
            model_name = settings.MODELS[idx]
            next_idx = (start_index + attempt + 1) % total_models
            next_model = settings.MODELS[next_idx]

            overall_start_time = time.time()
            first_token_time = None
            tool_start_times = {}
        
            messages = get_memory(history)
            if user.is_authenticated:
                prompt = SYSTEM_PROMPT + f"\n\nAuthenticated User Information: Name: {user.first_name} {user.last_name}, Email: {user.email}."
            else:
                prompt = SYSTEM_PROMPT
            messages.extend([SystemMessage(content=prompt),HumanMessage(content=message)])

            yield {
                            "type": "agent_thinking",
                            "message": "Analyzing your request",
                            "model": model_name,
                            "duration": 0.0,
                            "elapsed": 0.0,
                            "timestamp": time.time()
                        }
            try:
                model = get_llm(model_name=model_name)
                intent = await classify_intent(
                            message,
                            model
                        )
                        
                yield {
                        "type": "agent_thinking",
                        "message": f"Executing {intent} agent"
                    }
                state = {
                            "user": user,
                            "message": message,
                            "messages": messages,
                            "intent": intent,
                            "model": model
                        }
                        
                rental_graph = RentalGraph(
                    model,
                    tools=get_private_tools(user) if user.is_authenticated else get_public_tools()
                )
                
                async for event in rental_graph.graph.astream_events(
                            state,
                            version="v2"
                        ):
                    event_type = event.get("event")
                    if event_type == "on_chain_stream" and event.get("name") == "initiate_booking":
                        chunk = event.get("data", {}).get("chunk", {})
                        if isinstance(chunk, dict) and not chunk.get("is_complete", True):
                            logger.info("Yielding missing booking details: %s", chunk.get("missing_fields"))
                            yield {
                                "type": "missing_details",
                                "missing_fields": chunk.get("missing_fields", []),
                                "pickup_location": chunk.get("pickup_location"),
                                "pickup_date": chunk.get("pickup_date"),
                                "pickup_time": chunk.get("pickup_time"),
                                "return_location": chunk.get("return_location"),
                                "return_date": chunk.get("return_date"),
                                "return_time": chunk.get("return_time"),
                                "car_id": chunk.get("car_id"),
                                "message": chunk.get("response") or chunk.get("message") or "Please fill in the rental details below to proceed:",
                                "result": chunk.get("result")
                            }
                            yield {
                                "type": "token",
                                "content": f"{chunk.get('response') or chunk.get('message') or 'Please fill in the rental details below to proceed:'}\n\n",
                                "model": model_name
                            }

                    if event_type == "on_tool_start":
                        tool_name = event.get("name")
                        tool_input = event.get("data", {}).get("input", {})
                        now_t = time.time()
                        tool_start_times[tool_name] = now_t

                        yield {
                            "type": "tool_start",
                            "tool": tool_name,
                            "input": tool_input,
                            "message": f"Executing {tool_name}...",
                            "description": f"Executed {tool_name} on host webpage.",
                            "duration": None,
                            "elapsed": max(0.01, round(now_t - overall_start_time, 2)),
                            "timestamp": now_t
                        }
                    elif event_type == "on_tool_end":
                        tool_name = event.get("name")
                        now_t = time.time()
                        start_t = tool_start_times.pop(tool_name, now_t)
                        tool_duration = max(0.01, round(now_t - start_t, 2))

                        output = event.get("data", {}).get("output", "")
                        content = getattr(output, "content", output)
                        if isinstance(content, str):
                            str_out = content
                        else:
                            str_out = json.dumps(content, default=str)
                        if not str_out:
                            str_out = "Tool completed without output."

                        yield {
                            "type": "tool_end",
                            "tool": tool_name,
                            "output": str_out,
                            "duration": tool_duration,
                            "elapsed": max(0.01, round(now_t - overall_start_time, 2)),
                            "timestamp": now_t
                        }

                    elif event_type == "on_chain_stream":
                        # Dynamic model output is already streamed by on_chat_model_stream. Only workflow response nodes should produce chat text from chain events.
                        event_name = event.get("name")
                        response_nodes = {
                            "booking",
                            "cancellation",
                            "select_or_verify_car",
                            "check_car",
                            "ask_confirmation",
                            "cancel_booking",
                        }
                        if event_name not in response_nodes:
                            continue

                        chunk = event.get("data", {}).get("chunk")
                        if chunk is None:
                            continue

                        # If select_or_verify_car found multiple candidate cars, emit a tool_end event so webpage automation displays them on the fleet page
                        if event_name == "select_or_verify_car" and isinstance(chunk, dict) and chunk.get("candidate_cars"):
                            now_t = time.time()
                            yield {
                                "type": "tool_end",
                                "tool": "show_fleet_cars",
                                "output": json.dumps({
                                    "status": "multiple_cars",
                                    "action": "show_fleet_cars",
                                    "location": chunk.get("result", {}).get("location") or chunk.get("pickup_location") or "",
                                    "candidate_cars": chunk.get("candidate_cars", [])
                                }),
                                "duration": 0.05,
                                "elapsed": max(0.01, round(now_t - overall_start_time, 2)),
                                "timestamp": now_t
                            }

                        if isinstance(chunk, dict):
                            value = chunk.get("response")
                        else:
                            value = getattr(chunk, "response", None)

                        if value is None:
                            continue

                        content = value if isinstance(value, str) else json.dumps(value, default=str)
                        if content:
                            yield {
                                "type": "token",
                                "content": f"{content}\n\n",
                                "model": model_name
                            }

                    elif event_type== "on_chain_end":
                        yield {
                            "type": "agent_thinking",
                            "message": "Streaming response"
                        }

                    elif event_type == "on_chat_model_stream":
                        chunk = event.get("data", {}).get("chunk")
                        if chunk:
                            now_t = time.time()
                            thought_dur = None
                            if first_token_time is None:
                                first_token_time = now_t
                                thought_dur = max(0.05, round(first_token_time - overall_start_time, 2))

                            content = getattr(chunk, "content", None)
                            if isinstance(content, str) and content:
                                token_evt = {
                                    "type": "token",
                                    "content": content,
                                    "model": model_name
                                }
                                if thought_dur is not None:
                                    token_evt["thought_duration"] = thought_dur
                                    token_evt["elapsed"] = max(0.01, round(now_t - overall_start_time, 2))
                                yield token_evt

                            elif isinstance(content, list):
                                # Some models return content blocks
                                for block in content:
                                    token_str = ""
                                    if isinstance(block, str) and block:
                                        token_str = block
                                    elif isinstance(block, dict) and block.get("text"):
                                        token_str = block["text"]

                                    if token_str:
                                        token_evt = {
                                            "type": "token",
                                            "content": token_str,
                                            "model": model_name
                                        }
                                        if thought_dur is not None:
                                            token_evt["thought_duration"] = thought_dur
                                            token_evt["elapsed"] = max(0.01, round(now_t - overall_start_time, 2))
                                            thought_dur = None
                                        yield token_evt

                end_time = time.time()
                total_duration = max(0.01, round(end_time - overall_start_time, 2))
                thought_duration = max(0.05, round((first_token_time or end_time) - overall_start_time, 2))

                # Retain this successful model as the starting model for future turns
                self.current_model_index = idx

                yield {
                    "type": "done",
                    "model": model_name,
                    "thought_duration": thought_duration,
                    "total_duration": total_duration,
                    "duration": total_duration,
                    "timestamp": end_time
                }
                return    

            except Exception as exc:
                now_t = time.time()
                elapsed = max(0.01, round(now_t - overall_start_time, 2))
                if is_request_too_large_error(exc):
                    logger.warning(
                        "AI request exceeded the provider payload limit (model: %s): %s",
                        model_name,
                        exc,
                    )
                    yield {
                        "type": "error",
                        "error_code": 413,
                        "error_type": "request_too_large",
                        "model": model_name,
                        "message": "The conversation history is too large. Please start a new chat and try again.",
                        "duration": elapsed,
                        "retryable": False,
                        "timestamp": now_t,
                    }
                    return
                if is_rate_limit_error(exc) or getattr(exc, "status_code", None) == 404:
                    logger.warning("Rate limit (429) hit in AI agent stream: (model: %s)", model_name)
                    if attempt < total_models - 1:
                        self.current_model_index = next_idx
                        yield {
                            "type": "switch_model",
                            "error_code": 429,
                            "error_type": "rate_limit",
                            "model": model_name,
                            "next_model": next_model,
                            "message": f"Switching model to {next_model}.",
                            "duration": elapsed,
                            "retryable": True,
                            "retry_after": 5,
                            "timestamp": now_t
                        }
                        continue
                    yield {
                        "type": "error",
                        "error_code": 429,
                        "error_type": "rate_limit",
                        "model": model_name,
                        "message": "AI service is currently experiencing high demand (Rate limit reached). Please wait a few moments and try again.",
                        "duration": elapsed,
                        "retryable": True,
                        "retry_after": 5,
                        "timestamp": now_t
                    }
                    return
                else:
                    logger.exception("Error in AI agent stream execution: %s", exc)
                    yield {
                        "type": "error",
                        "error_code": 500,
                        "message": "The assistant encountered an issue processing your request. Please try again.",
                        "duration": elapsed,
                        "retryable": True,
                        "timestamp": now_t
                    }
                    return


rental_agent = RentalAgent()