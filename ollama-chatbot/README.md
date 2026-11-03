# Ollama Chatbot

A command-line chatbot powered by **Llama 3.2** running locally through [Ollama](https://ollama.com).

## Setup

1. Install Ollama and pull the model:
   ```bash
   ollama pull llama3.2
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Configure settings (optional):
   ```bash
   cp .env.example .env
   ```
4. Run:
   ```bash
   python main.py
   ```

## Commands
`/clear` reset conversation, `/help` show help, `/exit` quit.

## Structure
```
main.py              CLI entry point
src/chatbot/
  config.py          settings from .env
  chat.py            Ollama client + history
  logger.py          file logging
logs/                runtime logs (git-ignored)
```
