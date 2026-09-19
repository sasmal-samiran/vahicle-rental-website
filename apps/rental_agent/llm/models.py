import os 
from typing import Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_groq import ChatGroq

def get_llm(
    model_name: Optional[str] = None,
    temperature: float = 0.2
) -> BaseChatModel:
    api_key = os.getenv("API_KEY")
    model = model_name or os.getenv("LLM") or "openai/gpt-oss-120b"

    if not api_key:
        raise ValueError("GROQ / AI API key not configured!")
        
    return ChatGroq(
        model_name=model,
        groq_api_key=api_key,
        temperature=temperature,
        max_retries=2,
        timeout=60,
        streaming=True
    )