"""Application settings loaded from environment variables / .env file."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    model: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    temperature: float = float(os.getenv("TEMPERATURE", "0.7"))
    system_prompt: str = os.getenv(
        "SYSTEM_PROMPT", "You are a helpful, concise and friendly AI assistant."
    )
    max_history: int = int(os.getenv("MAX_HISTORY", "20"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()


settings = Settings()
