# main.py — Brain Brew (Professor/Student Quiz System)
# Features: RAG authoring (optional), LLM MCQ generation, prof-configurable total timer,
# student countdown with auto-submit, attempt analytics, animated hero + landing art.

import streamlit as st
import config as cfg

# Import extracted modules
from ui.theme import inject_theme, BRAIN_SVG, PROF_SVG, STUDENT_SVG
from views.professor import render_professor
from views.student import render_student

# ============================ App scaffolding ============================
st.set_page_config(page_title="Brain Brew", page_icon="🧠", layout="wide")
inject_theme()
st.markdown(f"""
<div class="hero">
  <div class="logo-wrap float-brain">{BRAIN_SVG}</div>
  <div class="brand float-title">
    <span class="gradient-text">Brain</span> <span class="accent">Brew</span>
  </div>
  <div class="tagline">LLM Quiz Engine</div>
</div>
""", unsafe_allow_html=True)

# Session defaults
for k, v in {
    "role": None, "prof_auth": False, "questions": [], "build_time": 0.0,
    "results": None, "current_quiz_id": None,
    "llm_calls": 0, "llm_cost": 0.0,
    "last_build_calls": 0, "last_build_cost": 0.0, "last_questions": 0,
    "student_ready": False,
    # timer
    "total_time_sec": 0, "quiz_end_ts": None, "quiz_start_ts": None, "auto_submitted": False,
    "prof_total_time_min": None,
}.items():
    if k not in st.session_state: st.session_state[k] = v

# ---------- Landing: Role selection (with art) ----------
colA, colB = st.columns(2)
with colA:
    st.markdown(PROF_SVG, unsafe_allow_html=True)
    st.caption("Teach, build quizzes, and review attempts.")
    if st.button("I'm a Professor", use_container_width=True, key="btn_prof"):
        st.session_state.prof_auth = False  # force login each time
        st.session_state.role = "prof"
with colB:
    st.markdown(STUDENT_SVG, unsafe_allow_html=True)
    st.caption("Join with a code and take the quiz.")
    if st.button("I'm a Student", use_container_width=True, key="btn_student"):
        # clear stale state on switch
        for k in [k for k in list(st.session_state.keys()) if k.startswith("q_mcq_")]:
            st.session_state.pop(k, None)
        st.session_state.questions = []
        st.session_state.results = None
        st.session_state.current_quiz_id = None
        st.session_state.student_ready = False
        st.session_state.total_time_sec = 0
        st.session_state.quiz_end_ts = None
        st.session_state.quiz_start_ts = None
        st.session_state.auto_submitted = False
        st.session_state.role = "student"

st.markdown("---")

# =============== Sidebar: gated — visible only AFTER professor logs in ===============
if st.session_state.role == "prof":
    if not st.session_state.prof_auth:
        st.sidebar.header("Professor")
        st.sidebar.info("🔒 Please sign in to access quiz settings.")
    else:
        st.sidebar.header("Quiz Settings (professor)")
        
        # Save sidebar config objects to session state right away so `views/professor.py` can grab it:
        st.session_state.prof_focus_terms = st.sidebar.text_input("Focus terms (optional)", "")
        st.session_state.prof_num_q = st.sidebar.slider("Number of questions", 4, 20, 10)
        st.session_state.prof_difficulty = st.sidebar.select_slider("Difficulty", options=["easy","medium","hard"], value="medium")
        st.session_state.prof_k_chunks = st.sidebar.slider("Context breadth (top-k chunks)", 2, 12, 8)
        st.session_state.prof_shuffle_choices = st.sidebar.toggle("Shuffle choices", True)
        st.session_state.prof_show_explanations_to_students = st.sidebar.toggle("Show explanations to students", True)
        st.session_state.prof_enforce_exact = st.sidebar.toggle(
            "Enforce exact count (may use extra LLM call)",
            value=bool(getattr(cfg, "ENFORCE_EXACT_RETRY", False))
        )
        default_total_min = max(2, int(round(2 * st.session_state.prof_num_q)))
        
        # Note: changing the number input here maps directly to session_state with the `key=`
        st.sidebar.number_input(
            "Total time (minutes)", min_value=2, step=1,
            value=st.session_state.get("prof_total_time_min") or default_total_min,
            key="prof_total_time_min",
            help="Default is 2 minutes per question; adjust total time as needed (min 2)."
        )

        _detected_key = cfg.get_api_key()
        if _detected_key: st.sidebar.success("API key detected — LLM enabled.")
        else:             st.sidebar.warning("No API key — demo mode (no external LLM calls).")
else:
    # Student-safe defaults
    st.session_state.prof_focus_terms = ""
    st.session_state.prof_num_q = 10
    st.session_state.prof_difficulty = "medium"
    st.session_state.prof_k_chunks = 8
    st.session_state.prof_shuffle_choices = True
    st.session_state.prof_show_explanations_to_students = False
    st.session_state.prof_enforce_exact = False
    _detected_key = cfg.get_api_key()

# ============================ Routes ============================
if st.session_state.role == "prof":
    render_professor()
elif st.session_state.role == "student":
    render_student()
else:
    st.info("Choose a role to continue: Professor or Student.")
