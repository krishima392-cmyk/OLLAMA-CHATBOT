"""Logging setup (file only, so the chat UI stays clean)."""
import logging
from pathlib import Path

from .config import settings


def get_logger(name: str = "chatbot") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(settings.log_level)
    log_dir = Path(__file__).resolve().parents[2] / "logs"
    log_dir.mkdir(exist_ok=True)

    handler = logging.FileHandler(log_dir / "chatbot.log", encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    logger.addHandler(handler)
    return logger
