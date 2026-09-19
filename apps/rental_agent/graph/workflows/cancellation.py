from langgraph.graph import StateGraph, END
from ..state import AgentState


def find_booking(state):
    return {
        "result": {
            "booking_id": 123,
            "status": "CONFIRMED"
        },
        "response": "Finding your booking..."
    }


def cancel_booking(state):
    return {
        "response": "Your booking has been cancelled."
    }


def build_cancel_graph():

    graph = StateGraph(AgentState)

    graph.add_node("find_booking", find_booking)
    graph.add_node("cancel_booking", cancel_booking)

    graph.set_entry_point("find_booking")

    graph.add_edge("find_booking", "cancel_booking")
    graph.add_edge("cancel_booking", END)

    return graph.compile()