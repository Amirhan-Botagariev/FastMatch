from app.core.config import settings
from app.integrations.llm.base import LLMClient
from app.integrations.llm.gemini_client import GeminiClient
from app.integrations.llm.openai_client import OpenAIClient

from app.core.debugger import debug


def create_llm_client() -> LLMClient:
    provider = settings.LLM_PROVIDER

    if provider == "gemini":
        return GeminiClient()

    if provider == "openai":
        return OpenAIClient()

    raise ValueError(f"Unsupported LLM provider: {provider}")