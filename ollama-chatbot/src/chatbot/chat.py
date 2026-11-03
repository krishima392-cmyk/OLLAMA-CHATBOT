"""Core chatbot logic: talks to Ollama and manages conversation history."""
from typing import Iterator

import ollama

from .config import settings
from .logger import get_logger

log = get_logger(__name__)


class ChatBot:
    def __init__(self) -> None:
        self.client = ollama.Client(host=settings.ollama_host)
        self.history: list[dict] = []
        self.clear()

    def clear(self) -> None:
        """Reset the conversation, keeping only the system prompt."""
        self.history = [{"role": "system", "content": settings.system_prompt}]
        log.info("Conversation cleared")

    def _trim_history(self) -> None:
        """Keep the system prompt + the last N messages."""
        system, rest = self.history[0], self.history[1:]
        if len(rest) > settings.max_history:
            self.history = [system] + rest[-settings.max_history:]

    def check_model(self) -> bool:
        """Return True if the configured model is available locally."""
        models = self.client.list()
        names = [m.model for m in models.models]
        return any(n == settings.model or n.startswith(f"{settings.model}:") for n in names)

    def stream_reply(self, user_input: str) -> Iterator[str]:
        """Send a message and yield the reply token by token."""
        self.history.append({"role": "user", "content": user_input})
        self._trim_history()
        log.info("User: %s", user_input)

        full_reply = ""
        try:
            stream = self.client.chat(
                model=settings.model,
                messages=self.history,
                stream=True,
                options={"temperature": settings.temperature},
            )
            for chunk in stream:
                token = chunk["message"]["content"]
                full_reply += token
                yield token
        except Exception:
            self.history.pop()  # drop the failed user message
            raise

        self.history.append({"role": "assistant", "content": full_reply})
        log.info("Assistant: %s", full_reply)
