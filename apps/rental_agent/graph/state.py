from typing import Annotated, TypedDict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict, total=False):
    # Base Conversation & Agent State
    user: Any
    message: str
    messages: Annotated[list[BaseMessage], add_messages]
    intent: str
    model: Any
    result: Any
    response: str

    # Booking & Workflow Fields
    car_id: int
    pickup_location: str
    pickup_date: str
    pickup_time: str
    return_location: str
    return_date: str
    return_time: str
    missing_fields: list[str]
    is_complete: bool
    is_car_resolved: bool
    is_available: bool
    candidate_cars: list[dict]
    quote: dict
    brand: str
    model_name: str
    category: str
    seats: int
    suggest: bool


