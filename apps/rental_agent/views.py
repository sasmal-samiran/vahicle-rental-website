import json
import time
import asyncio
import queue
import threading
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .agent import rental_agent, is_rate_limit_error
from utils.logger import get_logger

logger = get_logger("rental_agent")

def generate_sse_stream(user, user_input, history, last_model=None):
    """
    Consumes the async LangChain agent task and yields synchronous SSE frames
    via a thread-safe Queue, ensuring compatibility with WSGI/ASGI without warnings.
    """
    q = queue.Queue()
    SENTINEL = object()
    start_time = time.time()

    def run_agent_coroutine():
        async def _execute():
            try:
                async for event in rental_agent.execute_task(
                    user=user,
                    message=user_input,
                    history=history,
                    last_model=last_model
                ):
                    q.put(f"data: {json.dumps(event)}\n\n")
            except Exception as exc:
                elapsed = max(0.01, round(time.time() - start_time, 2))
                if is_rate_limit_error(exc):
                    logger.warning("Rate limit (429) caught in SSE agent stream: %s", exc)
                    q.put(f"data: {json.dumps({'type': 'error', 'error_code': 429, 'error_type': 'rate_limit', 'message': 'AI service is currently experiencing high demand (Rate limit reached). Please wait a few moments and try again.', 'duration': elapsed, 'retryable': True, 'retry_after': 5})}\n\n")
                else:
                    logger.exception("Error in SSE agent stream execution")
                    q.put(f"data: {json.dumps({'type': 'error', 'error_code': 500, 'message': 'The assistant encountered an issue processing your request. Please try again.', 'duration': elapsed, 'retryable': True})}\n\n")
            finally:
                q.put(SENTINEL)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_execute())
        finally:
            loop.close()

    worker_thread = threading.Thread(target=run_agent_coroutine, daemon=True)
    worker_thread.start()

    while True:
        chunk = q.get()
        if chunk is SENTINEL:
            break
        yield chunk


class BaseRentalAgentView(APIView):
    def post(self, request):
        user_input = request.data.get("message", "")
        history = request.data.get("history", [])
        last_model = request.data.get("model") or request.data.get("last_model")

        if not user_input or not str(user_input).strip():
            return Response(
                {"error": "Message parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        response = StreamingHttpResponse(
            generate_sse_stream(user=request.user, user_input=user_input, history=history, last_model=last_model),
            content_type="text/event-stream"
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        response["Access-Control-Allow-Origin"] = "*"
        return response


class PublicRentalAgentView(BaseRentalAgentView):
    permission_classes = [permissions.AllowAny]


class PrivateRentalAgentView(BaseRentalAgentView):
    permission_classes = [permissions.IsAuthenticated]
