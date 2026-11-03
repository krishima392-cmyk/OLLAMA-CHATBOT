"""CLI entry point for the Ollama chatbot."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import ollama
from rich.console import Console
from rich.panel import Panel

from chatbot.chat import ChatBot
from chatbot.config import settings
from chatbot.logger import get_logger

console = Console()
log = get_logger("main")

HELP = "[dim]Commands: /clear = reset chat | /help = show help | /exit = quit[/dim]"


def main() -> None:
    bot = ChatBot()

    try:
        if not bot.check_model():
            console.print(
                f"[red]Model '{settings.model}' not found.[/red]\n"
                f"Run: [bold]ollama pull {settings.model}[/bold]"
            )
            return
    except Exception:
        console.print(
            f"[red]Cannot reach Ollama at {settings.ollama_host}.[/red]\n"
            "Make sure Ollama is running: [bold]ollama serve[/bold]"
        )
        return

    console.print(
        Panel.fit(
            f"[bold cyan]Ollama Chatbot[/bold cyan]\nModel: {settings.model}",
            border_style="cyan",
        )
    )
    console.print(HELP)

    while True:
        try:
            user_input = console.input("\n[bold green]You:[/bold green] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Goodbye![/yellow]")
            break

        if not user_input:
            continue
        if user_input.lower() in {"/exit", "/quit"}:
            console.print("[yellow]Goodbye![/yellow]")
            break
        if user_input.lower() == "/clear":
            bot.clear()
            console.print("[dim]Conversation cleared.[/dim]")
            continue
        if user_input.lower() == "/help":
            console.print(HELP)
            continue

        console.print("[bold blue]Bot:[/bold blue] ", end="")
        try:
            for token in bot.stream_reply(user_input):
                console.print(token, end="", markup=False, highlight=False)
            console.print()
        except ollama.ResponseError as e:
            log.error("Ollama error: %s", e)
            console.print(f"\n[red]Ollama error: {e.error}[/red]")
        except Exception as e:
            log.exception("Unexpected error")
            console.print(f"\n[red]Something went wrong: {e}[/red]")


if __name__ == "__main__":
    main()
