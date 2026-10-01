from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, SystemMessage

from .state import AgentState
from .router import route_intent, route_tools
from .workflows.booking import build_booking_graph
from .workflows.cancellation import build_cancel_graph
from ..tools.tools import create_tools
from utils.logger import get_logger

logger = get_logger("rental_agent")

class RentalGraph:
    def __init__(self, model, tools=None):
        self.model = model
        self.tools = tools() if callable(tools) else (tools or [])
        self.model_with_tools = model.bind_tools(self.tools)
        self.tool_node = ToolNode(self.tools)
        self.booking_graph = (
            build_booking_graph()
        )
        self.cancellation_graph = (
            build_cancel_graph()
        )
        self.graph = self.build_graph()

    async def router_node(
        self,
        state: AgentState
    ):
        return state


    async def dynamic_node(
        self,
        state: AgentState
    ):
        messages = state.get("messages") or [HumanMessage(content=state["message"])]
        try:
            response = await self.model_with_tools.ainvoke(messages)
        except Exception as exc:
            if "tool calling" not in str(exc).lower():
                raise

            logger.warning(
                "Model does not support tool calling; retrying without tools: %s",
                exc,
            )
            fallback_messages = [
                SystemMessage(content="Respond without using tools for this request."),
                *messages,
            ]
            response = await self.model.ainvoke(fallback_messages)
        return {
            "messages": [response],
            "response": response.content or "",
        }
        

    async def booking_node(
        self,
        state: AgentState
    ):
        user = state.get("user")
        is_authenticated = bool(user and getattr(user, "is_authenticated", False))
        if not is_authenticated:
            tools_map = create_tools(user)
            await tools_map["open_login_modal"].ainvoke({})
            return {
                "result": {"status": "auth_required", "action": "open_login_modal"},
                "response": "Please sign in to proceed with your booking. I have opened the sign-in window for you."
            }
        return await self.booking_graph.ainvoke(state)

    async def cancellation_node(
        self,
        state: AgentState
    ):
        user = state.get("user")
        is_authenticated = bool(user and getattr(user, "is_authenticated", False))
        if not is_authenticated:
            tools_map = create_tools(user)
            await tools_map["open_login_modal"].ainvoke({})
            return {
                "result": {"status": "auth_required", "action": "open_login_modal"},
                "response": "Please sign in to manage or cancel your reservations. I have opened the sign-in window for you."
            }
        result = await self.cancellation_graph.ainvoke(state)
        return {
            "result": result.get("result"),
            "response": result.get("response")
        }

    def build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node(
            "router",
            self.router_node
        )
        graph.add_node(
            "booking",
            self.booking_node
        )
        graph.add_node(
            "cancellation",
            self.cancellation_node
        )
        graph.add_node(
            "dynamic",
            self.dynamic_node
        )
        graph.add_node("tools", self.tool_node)
        graph.set_entry_point(
            "router"
        )
        graph.add_conditional_edges(
            "router",
            route_intent,
            {
                "booking": "booking",
                "cancellation": "cancellation",
                "dynamic": "dynamic"
            }
        )
        graph.add_edge(
            "booking",
            END
        )
        graph.add_edge(
            "cancellation",
            END
        )
        graph.add_conditional_edges("dynamic", route_tools)
        graph.add_edge("tools", "dynamic")
        return graph.compile()