from pydantic import BaseModel
from typing import List

class Settings(BaseModel):
    MODELS: List[str] = [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "openai/gpt-oss-safeguard-20b",
        "groq/compound",
        "groq/compound-mini"
    ]

settings = Settings()
