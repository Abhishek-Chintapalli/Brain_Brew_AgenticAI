import streamlit as st

# Optional live refresh for the student countdown
try:
    from streamlit_autorefresh import st_autorefresh  # pip install streamlit-autorefresh
except Exception:
    st_autorefresh = None

def _fmt_mmss(seconds: int) -> str:
    seconds = max(0, int(seconds))
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"

def tick_every(ms: int, key: str):
    """Refresh every `ms` ms. Uses st_autorefresh if available; else a JS fallback."""
    if st_autorefresh:
        st_autorefresh(interval=ms, key=key)
    else:
        st.markdown(f"<script>setTimeout(()=>window.location.reload(), {ms});</script>", unsafe_allow_html=True)
