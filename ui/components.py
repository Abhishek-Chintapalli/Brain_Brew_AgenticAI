from typing import List, Dict
import streamlit as st
from core.llm import LLMInterface

def render_agents_kpis(llm: LLMInterface):
    cols = st.columns(5)
    cards = [
        ("🗂️ DocumentProcessor", "Ingest PDF/TXT, chunk + embed", "0 LLM"),
        ("🧠 ContentAnalyzer",   "Generate MCQs",                "1 LLM"),
        ("🖥️ UI Renderer",       "Render quiz & capture answers",   "0 LLM"),
        ("✅ Grader",            "Server-side scoring",          "0 LLM"),
        ("📊 Store",             "Persist quizzes/attempts",     "0 LLM"),
    ]
    for i,(title,sub,llms) in enumerate(cards):
        with cols[i]:
            st.markdown(
                f"<div class='card'><div class='title'>{title}</div>"
                f"<div class='sub'>{sub}</div><div class='chip'>{llms}</div></div>",
                unsafe_allow_html=True
            )
    calls = st.session_state.get("llm_calls", 0)
    cost  = st.session_state.get("llm_cost",  0.0)
    build = st.session_state.get("build_time", 0.0)
    m1, m2, m3 = st.columns(3)
    m1.metric("LLM calls", calls)
    m2.metric("Mode", "LLM" if llm.enabled else "Demo")
    m3.metric("Build time (sec)", f"{build:.2f}")
    st.caption(f"Est. cost: ${cost:.4f}")

def render_quiz_mcq(questions: List[Dict], disable: bool = False):
    st.subheader("📚 Quiz")
    answered = 0
    for i, q in enumerate(questions):
        st.markdown(f"**Q{i+1}. {q['question']}**")
        options = list(range(4))
        key = f"q_mcq_{i}"
        prior = st.session_state.get(key, None)
        st.radio(
            label="", label_visibility="collapsed",
            options=options,
            format_func=lambda idx, opts=q["options"]: opts[idx],
            key=key,
            index=None if prior is None else options.index(prior),
            disabled=disable,
        )
        if st.session_state.get(key, None) is not None:
            answered += 1
    st.caption(f"Progress: {answered}/{len(questions)} answered")
