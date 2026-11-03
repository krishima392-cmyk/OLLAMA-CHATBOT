"""Enterprise-style Streamlit UI for the Ollama chatbot.

Run with:  streamlit run app.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import streamlit as st

from chatbot.config import settings
from chatbot.service import StreamStats, list_models, stream_chat

# ----------------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Enterprise AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    #MainMenu, footer {visibility: hidden;}
    .block-container {padding-top: 1.5rem; max-width: 900px;}

    /* Header banner */
    .app-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 60%, #3B82F6 100%);
        padding: 1.4rem 1.8rem; border-radius: 16px; color: #fff;
        box-shadow: 0 8px 24px rgba(37, 99, 235, .25); margin-bottom: 1.2rem;
    }
    .app-header h1 {margin: 0; font-size: 1.6rem; font-weight: 700; color: #fff;}
    .app-header p {margin: .3rem 0 0; opacity: .85; font-size: .92rem;}

    /* Status pill */
    .pill {
        display: inline-block; padding: .2rem .7rem; border-radius: 999px;
        font-size: .78rem; font-weight: 600;
    }
    .pill-ok {background: #DCFCE7; color: #166534;}
    .pill-err {background: #FEE2E2; color: #991B1B;}

    /* Chat bubbles */
    [data-testid="stChatMessage"] {
        background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px;
        padding: 1rem 1.2rem; margin-bottom: .7rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, .05);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {border-right: 1px solid #E2E8F0;}
    .sidebar-title {
        font-size: .72rem; letter-spacing: .08em; font-weight: 700;
        color: #64748B; text-transform: uppercase; margin: 1rem 0 .3rem;
    }

    /* Stats caption */
    .stats {color: #64748B; font-size: .76rem; margin-top: .4rem;}

    /* Suggestion buttons */
    div.stButton > button {
        border-radius: 12px; border: 1px solid #CBD5E1; padding: .8rem 1rem;
        text-align: left; transition: all .15s ease;
    }
    div.stButton > button:hover {
        border-color: #2563EB; color: #2563EB; transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, .15);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------
DEFAULT_SYSTEM_PROMPT = settings.system_prompt

if "messages" not in st.session_state:
    st.session_state.messages = []  # [{"role", "content", "stats"?}]
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


@st.cache_data(ttl=10, show_spinner=False)
def get_models() -> tuple[list[str], str | None]:
    """Return (models, error). Cached briefly to avoid hammering Ollama."""
    try:
        return list_models(), None
    except Exception as exc:  # noqa: BLE001
        return [], str(exc)


models, conn_error = get_models()

# ----------------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🤖 AI Assistant")

    if conn_error:
        st.markdown('<span class="pill pill-err">● Ollama offline</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="pill pill-ok">● Ollama connected</span>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-title">Model</div>', unsafe_allow_html=True)
    if models:
        default_idx = next(
            (i for i, m in enumerate(models) if m.startswith(settings.model)), 0
        )
        model = st.selectbox("Model", models, index=default_idx, label_visibility="collapsed")
    else:
        model = settings.model
        st.caption(f"Using `{model}` (no models detected)")

    st.markdown('<div class="sidebar-title">Behaviour</div>', unsafe_allow_html=True)
    temperature = st.slider(
        "Creativity (temperature)", 0.0, 1.5, float(settings.temperature), 0.05,
        help="Lower = focused and deterministic. Higher = more creative.",
    )
    max_history = st.slider(
        "Memory (messages)", 2, 50, int(settings.max_history), 2,
        help="How many recent messages are sent to the model as context.",
    )
    system_prompt = st.text_area(
        "System prompt", value=DEFAULT_SYSTEM_PROMPT, height=110,
        help="Defines the assistant's role and tone.",
    )

    st.markdown('<div class="sidebar-title">Session</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    if col1.button("🗑 Clear", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    if col2.button("🔄 Refresh", use_container_width=True):
        get_models.clear()
        st.rerun()

    if st.session_state.messages:
        export = {
            "exported_at": datetime.now().isoformat(timespec="seconds"),
            "model": model,
            "messages": [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
        }
        st.download_button(
            "⬇ Export chat (JSON)",
            data=json.dumps(export, indent=2, ensure_ascii=False),
            file_name=f"chat_{datetime.now():%Y%m%d_%H%M%S}.json",
            mime="application/json",
            use_container_width=True,
        )

    st.divider()
    user_msgs = sum(1 for m in st.session_state.messages if m["role"] == "user")
    st.caption(f"💬 {user_msgs} message(s) this session")
    st.caption("🔒 Runs 100% locally. Your data never leaves this machine.")

# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="app-header">
        <h1>Enterprise AI Assistant</h1>
        <p>Powered by <b>{model}</b> via Ollama · Private, secure and local</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if conn_error:
    st.error(
        f"Cannot reach Ollama at `{settings.ollama_host}`. "
        "Start it with `ollama serve`, then click **Refresh** in the sidebar."
    )

# ----------------------------------------------------------------------------
# Welcome screen with suggestions
# ----------------------------------------------------------------------------
SUGGESTIONS = [
    ("📝 Draft an email", "Draft a professional email to a client about a project delay."),
    ("💡 Explain a concept", "Explain microservices architecture in simple terms."),
    ("🐍 Write code", "Write a Python function to validate email addresses with tests."),
    ("📊 Summarise ideas", "Give me a 5-point summary of best practices for remote team management."),
]

if not st.session_state.messages:
    st.markdown("##### How can I help you today?")
    cols = st.columns(2)
    for i, (title, prompt) in enumerate(SUGGESTIONS):
        if cols[i % 2].button(title, key=f"sugg_{i}", use_container_width=True):
            st.session_state.pending_prompt = prompt
            st.rerun()

# ----------------------------------------------------------------------------
# Render history
# ----------------------------------------------------------------------------
AVATARS = {"user": "🧑‍💼", "assistant": "🤖"}


def render_stats(stats: dict | None) -> None:
    if stats and stats.get("tokens"):
        st.markdown(
            f'<div class="stats">⚡ {stats["tokens_per_sec"]:.1f} tokens/s · '
            f'{stats["tokens"]} tokens · {stats["seconds"]:.1f}s</div>',
            unsafe_allow_html=True,
        )


for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=AVATARS[msg["role"]]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            render_stats(msg.get("stats"))

# ----------------------------------------------------------------------------
# Input handling
# ----------------------------------------------------------------------------
prompt = st.chat_input("Type your message...", disabled=bool(conn_error))
if st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=AVATARS["user"]):
        st.markdown(prompt)

    # Build payload: system prompt + trimmed history (no UI-only fields)
    recent = st.session_state.messages[-max_history:]
    payload = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]} for m in recent
    ]

    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
        stats = StreamStats()
        try:
            with st.spinner("Thinking..."):
                stream = stream_chat(payload, model, temperature, stats)
                first = next(stream, "")

            def token_gen():
                yield first
                yield from stream

            reply = st.write_stream(token_gen())
            stats_dict = {
                "tokens": stats.tokens,
                "seconds": stats.seconds,
                "tokens_per_sec": stats.tokens_per_sec,
            }
            render_stats(stats_dict)
            st.session_state.messages.append(
                {"role": "assistant", "content": reply, "stats": stats_dict}
            )
        except Exception as exc:  # noqa: BLE001
            st.session_state.messages.pop()  # remove the unanswered user message
            st.error(f"Something went wrong: {exc}")
