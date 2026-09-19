import json
import re
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from ..state import AgentState
from ...tools.booking_tools import collect_details, resolve_booking_car, check_availability
from apps.vehicles.models import Car
from apps.vehicles.serializers import parse_datetime_param
from apps.bookings.services import PricingService
from utils.logger import get_logger

logger = get_logger("booking_agent")


async def initiate_booking(state: AgentState):
    args = {
        "car_id": state.get("car_id"),
        "pickup_location": state.get("pickup_location"),
        "pickup_date": state.get("pickup_date"),
        "pickup_time": state.get("pickup_time"),
        "return_location": state.get("return_location"),
        "return_date": state.get("return_date"),
        "return_time": state.get("return_time"),
        "brand": state.get("brand"),
        "model": state.get("model_name"),
        "category": state.get("category"),
        "seats": state.get("seats"),
        "suggest": state.get("suggest"),
    }

    # If car_id was mentioned in message as #ID or Car ID: ID
    msg_text = state.get("message") or ""
    if not args.get("car_id") and msg_text:
        m = re.search(r'(?:car\s*id|car\s*#|id\s*#|#|\bid\s*:?\s*)(\d+)', msg_text, re.IGNORECASE)
        if m:
            try:
                args["car_id"] = int(m.group(1))
            except ValueError:
                pass

    model = state.get("model")
    # If key fields are missing, attempt extraction from conversation messages using LLM tool calling
    if model and not (args.get("pickup_location") and args.get("pickup_date") and args.get("return_date")):
        try:
            model_with_tool = model.bind_tools([collect_details])
            messages = state.get("messages") or []
            if not messages and msg_text:
                messages = [HumanMessage(content=msg_text)]

            extract_prompt = [
                SystemMessage(
                    content=(
                        "You are a luxury car rental assistant. Extract booking details from the user conversation "
                        "using the collect_details tool. Extract pickup_location, pickup_date, pickup_time, return_location, "
                        "return_date, return_time, car_id, brand, model, category, seats, and suggest (set suggest=true if the user asks for suggestions/recommendations). "
                        "If a field is not provided, leave it null/None."
                    )
                ),
                *messages
            ]
            response = await model_with_tool.ainvoke(extract_prompt)
            if getattr(response, "tool_calls", None):
                extracted = response.tool_calls[0].get("args", {})
                for k, v in extracted.items():
                    if v is not None and not args.get(k):
                        args[k] = v
        except Exception as exc:
            logger.warning("Could not extract details via model in initiate_booking: %s", exc)

    result = await collect_details.ainvoke(args)
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except Exception:
            pass

    is_complete = result.get("is_complete", False) if isinstance(result, dict) else False
    missing_fields = result.get("missing_fields", []) if isinstance(result, dict) else []
    response_msg = result.get("response") or result.get("message") if isinstance(result, dict) else str(result)
    car_id = (result.get("car_id") if isinstance(result, dict) else None) or args.get("car_id")
    brand = (result.get("brand") if isinstance(result, dict) else None) or args.get("brand")
    model_name = (result.get("model") if isinstance(result, dict) else None) or args.get("model") or args.get("model_name")
    category = (result.get("category") if isinstance(result, dict) else None) or args.get("category")
    seats = (result.get("seats") if isinstance(result, dict) else None) or args.get("seats")
    suggest = (result.get("suggest") if isinstance(result, dict) else None) or args.get("suggest")

    return {
        "pickup_location": (result.get("pickup_location") if isinstance(result, dict) else None) or args.get("pickup_location"),
        "pickup_date": (result.get("pickup_date") if isinstance(result, dict) else None) or args.get("pickup_date"),
        "pickup_time": (result.get("pickup_time") if isinstance(result, dict) else None) or args.get("pickup_time"),
        "return_location": (result.get("return_location") if isinstance(result, dict) else None) or args.get("return_location"),
        "return_date": (result.get("return_date") if isinstance(result, dict) else None) or args.get("return_date"),
        "return_time": (result.get("return_time") if isinstance(result, dict) else None) or args.get("return_time"),
        "car_id": car_id,
        "brand": brand,
        "model_name": model_name,
        "category": category,
        "seats": seats,
        "suggest": suggest or False,
        "missing_fields": missing_fields,
        "is_complete": is_complete,
        "is_car_resolved": False,
        "result": result,
        "response": response_msg
    }


async def select_or_verify_car(state: AgentState):
    pickup_loc = state.get("pickup_location")
    pickup_date = state.get("pickup_date")
    return_date = state.get("return_date")
    car_id = state.get("car_id")
    brand = state.get("brand")
    model_name = state.get("model_name")
    category = state.get("category")
    seats = state.get("seats")
    suggest = state.get("suggest", False)

    res = await resolve_booking_car.ainvoke({
        "pickup_location": pickup_loc,
        "pickup_date": pickup_date,
        "return_date": return_date,
        "car_id": car_id,
        "brand": brand,
        "model": model_name,
        "category": category,
        "seats": seats,
        "suggest": suggest,
    })

    if isinstance(res, str):
        try:
            res = json.loads(res)
        except Exception:
            res = {"status": "error", "message": res, "response": res, "is_car_resolved": False}

    is_resolved = res.get("is_car_resolved", False) if isinstance(res, dict) else False
    resolved_car_id = res.get("car_id") if (isinstance(res, dict) and is_resolved) else None
    response_msg = (res.get("response") or res.get("message")) if isinstance(res, dict) else str(res)

    return {
        "car_id": resolved_car_id or car_id,
        "is_car_resolved": is_resolved,
        "candidate_cars": res.get("candidate_cars", []) if isinstance(res, dict) else [],
        "result": res,
        # If car is resolved, we will let ask_confirmation provide the complete pricing summary.
        # If car is not resolved (e.g. multiple cars list, suggestion, location mismatch), response is output to user.
        "response": None if is_resolved else response_msg
    }


async def check_car(state: AgentState):
    car_id = state.get("car_id")
    pickup_date = state.get("pickup_date")
    return_date = state.get("return_date")

    result = await check_availability.ainvoke({
        "car_id": car_id,
        "pickup_date": pickup_date,
        "return_date": return_date,
    })

    if isinstance(result, str):
        try:
            result = json.loads(result)
        except Exception:
            pass

    is_avail = result.get("available", False) if isinstance(result, dict) else False
    msg = result.get("message") if isinstance(result, dict) else str(result)

    return {
        "result": result,
        "is_available": is_avail,
        "response": None if is_avail else (msg or "The selected vehicle is unavailable for the chosen dates.")
    }


def calculate_price(state: AgentState):
    car_id = state.get("car_id")
    pickup_date = state.get("pickup_date")
    return_date = state.get("return_date")

    try:
        car = Car.objects.select_related("category", "location").get(id=car_id)
        pickup_dt = parse_datetime_param(pickup_date, is_end=False)
        return_dt = parse_datetime_param(return_date, is_end=True)

        quote = PricingService.calculate_quote(car, pickup_dt, return_dt)
        return {
            "quote": quote,
            "result": quote
        }
    except Exception as exc:
        logger.error("Error calculating quote for car %s: %s", car_id, exc)
        return {
            "quote": {},
            "result": {"error": str(exc)}
        }


def ask_confirmation(state: AgentState):
    quote = state.get("quote") or {}
    car_id = state.get("car_id")
    pickup_loc = state.get("pickup_location")
    return_loc = state.get("return_location") or pickup_loc
    pickup_date = state.get("pickup_date")
    return_date = state.get("return_date")

    car_name = quote.get("car_name")
    if not car_name and car_id:
        try:
            c = Car.objects.get(id=car_id)
            car_name = f"{c.brand} {c.model}"
        except Exception:
            car_name = "Selected Vehicle"

    total_days = quote.get("total_days", 1)
    daily_rate = quote.get("daily_rate", 0.0)
    rental_charge = quote.get("rental_charge", 0.0)
    tax_amount = quote.get("tax_amount", 0.0)
    deposit_amount = quote.get("deposit_amount", 0.0)
    total_amount = quote.get("total_amount", 0.0)

    breakdown = (
        f"### 📋 Booking Summary & Confirmation\n\n"
        f"Here is your booking breakdown for the **{car_name}**:\n\n"
        f"• **Vehicle**: {car_name}\n"
        f"• **Pickup Location**: {pickup_loc}\n"
        f"• **Return Location**: {return_loc}\n"
        f"• **Rental Period**: {pickup_date} to {return_date} ({total_days} day{'s' if total_days > 1 else ''})\n"
        f"• **Daily Rate**: ₹{daily_rate:,.0f}/day\n"
        f"• **Rental Charge**: ₹{rental_charge:,.0f}\n"
        f"• **Standard GST / Tax (10%)**: ₹{tax_amount:,.0f}\n"
        f"• **Refundable Security Deposit**: ₹{deposit_amount:,.0f}\n"
        f"• **Total Estimated Amount**: **₹{total_amount:,.0f}**\n\n"
        f"Would you like to confirm and proceed with this reservation?"
    )

    return {
        "response": breakdown,
        "result": quote
    }


def route_initial_details(state: AgentState):
    if not state.get("is_complete", False):
        return END
    return "select_or_verify_car"


def route_car_selection(state: AgentState):
    if not state.get("is_car_resolved", False):
        return END
    return "check_car"


def route_car_availability(state: AgentState):
    if not state.get("is_available", True):
        return END
    return "calculate_price"


def build_booking_graph():
    graph = StateGraph(AgentState)

    graph.add_node("initiate_booking", initiate_booking)
    graph.add_node("select_or_verify_car", select_or_verify_car)
    graph.add_node("check_car", check_car)
    graph.add_node("calculate_price", calculate_price)
    graph.add_node("ask_confirmation", ask_confirmation)

    graph.set_entry_point("initiate_booking")

    graph.add_conditional_edges(
        "initiate_booking",
        route_initial_details,
        {
            "select_or_verify_car": "select_or_verify_car",
            END: END
        }
    )
    graph.add_conditional_edges(
        "select_or_verify_car",
        route_car_selection,
        {
            "check_car": "check_car",
            END: END
        }
    )
    graph.add_conditional_edges(
        "check_car",
        route_car_availability,
        {
            "calculate_price": "calculate_price",
            END: END
        }
    )
    graph.add_edge("calculate_price", "ask_confirmation")
    graph.add_edge("ask_confirmation", END)

    return graph.compile()