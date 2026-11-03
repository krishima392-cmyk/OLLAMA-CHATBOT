"""Reusable Ollama service layer (used by the Streamlit UI)."""
from dataclasses import dataclass
from typing import Iterator

import ollama

from .config import settings
from .logger import get_logger

log = get_logger(__name__)


@dataclass
class StreamStats:
    """Performance metrics filled in once a streamed reply finishes."""

    tokens: int = 0
    seconds: float = 0.0
    tokens_per_sec: float = 0.0


def _client() -> ollama.Client:
    return ollama.Client(host=settings.ollama_host)


def list_models() -> list[str]:
    """Return the names of all locally installed models."""
    response = _client().list()
    return sorted(m.model for m in response.models)


def stream_chat(
    messages: list[dict],
    model: str,
    temperature: float,
    stats: StreamStats | None = None,
) -> Iterator[str]:
    """Stream a reply token by token; optionally fill `stats` at the end."""
    log.info("Chat request | model=%s | messages=%d", model, len(messages))
    stream = _client().chat(
        model=model,
        messages=messages,
        stream=True,
        options={"temperature": temperature},
    )
    for chunk in stream:
        yield chunk["message"]["content"]

        if getattr(chunk, "done", False) and stats is not None:
            eval_count = getattr(chunk, "eval_count", 0) or 0
            eval_ns = getattr(chunk, "eval_duration", 0) or 0
            total_ns = getattr(chunk, "total_duration", 0) or 0
            stats.tokens = eval_count
            stats.seconds = total_ns / 1e9
            stats.tokens_per_sec = eval_count / (eval_ns / 1e9) if eval_ns else 0.0
