from langgraph.graph import END
from ..llm.prompts import INTENT_PROMT

async def classify_intent(message, llm):
    prompt = INTENT_PROMT.format(message)
    result = await llm.ainvoke(prompt)

    return result.content.strip().lower()

def route_intent(state):
    intent = state["intent"]
    if intent == "booking":
        return "booking"

    if intent == "cancellation":
        return "cancellation"

    return "dynamic"

def route_tools(state):
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    return "tools" if getattr(last_message, "tool_calls", None) else END