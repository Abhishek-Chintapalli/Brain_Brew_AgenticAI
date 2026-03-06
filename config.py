"""
config.py — Brain Brew (Professor/Student Quiz System)

API key lookup (in order):
1) API_KEY (here)
2) env/.env: OPENAI_API_KEY
3) st.secrets["OPENAI_API_KEY"] (if secrets.toml exists)

Set PROFESSOR_PASSCODE in .env for security.
QUIZ_STORE_PATH is the JSON store path.
"""

from __future__ import annotations
import os
from pathlib import Path

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except Exception:
    pass

# ------------ LLM / API ------------
API_KEY: str = os.getenv("API_KEY", "").strip()
MODEL_NAME: str = os.getenv("OPENAI_MODEL", "gpt-4o").strip()
OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com").strip()
CHAT_URL: str = f"{OPENAI_BASE_URL.rstrip('/')}/v1/chat/completions"

# Embeddings (for optional RAG)
RAG_EMBED_MODEL: str = os.getenv("RAG_EMBED_MODEL", "all-MiniLM-L6-v2").strip()

# LLM response settings
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "1500"))
COST_PER_CALL: float = float(os.getenv("COST_PER_CALL", "0.002"))

# Optional strict count retry
ENFORCE_EXACT_RETRY: bool = os.getenv("ENFORCE_EXACT_RETRY", "false").lower() in {"1","true","yes","on"}

# ------------ Auth ------------
PROFESSOR_PASSCODE: str = os.getenv("PROFESSOR_PASSCODE", "prof123").strip()
SESSION_COOKIE_NAME: str = os.getenv("SESSION_COOKIE_NAME", "quiz_role_session").strip()

# ------------ Storage ------------
QUIZ_STORE_PATH: str = os.getenv("QUIZ_STORE_PATH", "quiz_store.json").strip()

# ------------ Misc ------------
SENTINEL: int = -1  # unused placeholder for radios

# ------------ Helpers ------------
def _secrets_file_exists() -> bool:
    candidates = [
        Path.cwd() / ".streamlit" / "secrets.toml",
        Path.home() / ".streamlit" / "secrets.toml",
    ]
    env_path = os.getenv("STREAMLIT_SECRETS_FILE")
    if env_path:
        candidates.append(Path(env_path))
    return any(p.exists() for p in candidates)

def get_api_key() -> str:
    # 1) hardcoded here
    if API_KEY:
        return API_KEY
    # 2) env/.env
    env_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if env_key:
        return env_key
    # 3) st.secrets (only if file exists)
    if _secrets_file_exists():
        try:
            import streamlit as st
            secret = (st.secrets.get("OPENAI_API_KEY") or "").strip()
            if secret:
                return secret
        except Exception:
            pass
    return ""

def masked(key: str) -> str:
    if not key:
        return "(none)"
    return f"{key[:3]}…{key[-4:]}" if len(key) > 8 else "****"
