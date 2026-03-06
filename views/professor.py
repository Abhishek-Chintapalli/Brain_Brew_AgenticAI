import time
import io
import traceback
import uuid
import random
import streamlit as st
import config as cfg

from core.llm import get_llm
from core.analyzer import ContentAnalyzer, AnalysisConfig
from core.document import DocumentProcessor, extract_keywords
from core.storage import _load_store, _save_store, _gen_quiz_code
from utils.helpers import _fmt_mmss
from ui.components import render_agents_kpis

def render_professor():
    # Login gate
    if not st.session_state.prof_auth:
        st.subheader("Professor Login")
        with st.form("prof_login"):
            pw = st.text_input("Passcode", type="password")
            submitted = st.form_submit_button("Sign in")
            
        if submitted:
            if pw == cfg.PROFESSOR_PASSCODE:
                st.session_state.prof_auth = True
                st.rerun()
            else:
                st.error("Invalid passcode.")
                
        if not st.session_state.prof_auth:
            st.stop()

    # Agents dashboard & authoring
    llm = get_llm(cfg.get_api_key()); analyzer = ContentAnalyzer(llm)
    render_agents_kpis(llm)

    st.header("Authoring")
    uploaded = st.file_uploader("Upload course material (PDF or TXT)", type=["pdf","txt"])
    sample_txt = "Stacks are LIFO; queues are FIFO. Newton's laws govern motion; p=mv. Neural networks approximate functions."
    processor = DocumentProcessor()

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("🛠️ Build Quiz", use_container_width=True):
            for k in [k for k in list(st.session_state.keys()) if k.startswith("q_mcq_")]:
                st.session_state.pop(k, None)
            st.session_state.questions = []; st.session_state.results = None

            t0 = time.perf_counter()
            prev_calls = llm.call_count; prev_cost = llm.estimated_cost

            progress = st.progress(0, text="Processing document..."); time.sleep(0.05)
            try:
                if uploaded is not None:
                    if uploaded.name.lower().endswith(".pdf"):
                        data = uploaded.getvalue(); bio = io.BytesIO(data); bio.name = uploaded.name
                        doc = processor.process(bio)
                    else:
                        doc = processor.process(uploaded)
                else:
                    fake = io.BytesIO(sample_txt.encode("utf-8")); fake.name = "sample.txt"
                    doc = processor.process(fake)
            except Exception as e:
                doc = {"success": False, "error": f"Processing failed: {e}"}

            progress.progress(40, text="Selecting focused chunks ..."); time.sleep(0.05)
            try:
                # get properties from sidebar that were previously pushed to session_state or variables
                # (we will pass them as kwargs in the final refactor, or read them from session_state)
                focus_terms = st.session_state.get("prof_focus_terms", "")
                num_q = st.session_state.get("prof_num_q", 10)
                difficulty = st.session_state.get("prof_difficulty", "medium")
                k_chunks = st.session_state.get("prof_k_chunks", 8)
                shuffle_choices = st.session_state.get("prof_shuffle_choices", True)
                enforce_exact = st.session_state.get("prof_enforce_exact", False)

                query = (focus_terms.strip() or " ".join(extract_keywords(doc.get("text", sample_txt), top_k=8)) or "overview")
                if doc.get("success") and processor.vstore:
                    try:   top = processor.vstore.search(query, k=k_chunks)
                    except Exception: top = doc["chunks"][:k_chunks]
                else:
                    top = doc.get("chunks", [])[:k_chunks]

                cfgA = AnalysisConfig(num_questions=int(st.session_state.get("prof_total_time_min") and num_q or num_q),
                                      difficulty=difficulty)
                with st.spinner("Generating questions (LLM)..."):
                    quiz = analyzer.generate_mcqs(top, cfgA, enforce_exact=enforce_exact)

                qs = quiz["questions"]

                if shuffle_choices:
                    def _shuffle_one(q, seed):
                        idxs = list(range(4)); rnd = random.Random(seed); rnd.shuffle(idxs)
                        q["options"] = [q["options"][i] for i in idxs]
                        q["answer_index"] = idxs.index(q["answer_index"])
                        return q
                    base_seed = int(time.time())
                    qs = [_shuffle_one(dict(q), base_seed + i) for i, q in enumerate(qs)]

                st.session_state.questions = qs
                progress.progress(100, text=f"Quiz ready! ({len(qs)} questions)")

                st.session_state.llm_calls = llm.call_count
                st.session_state.llm_cost  = llm.estimated_cost
                st.session_state.last_build_calls = llm.call_count - prev_calls
                st.session_state.last_build_cost  = max(0.0, llm.estimated_cost - prev_cost)
                st.session_state.last_questions   = len(qs)

            except Exception as e:
                st.error(f"Quiz generation error: {e}")
                st.code(traceback.format_exc()); progress.progress(100, text="Failed."); st.stop()

            st.session_state.build_time = time.perf_counter() - t0
            st.rerun()

    with col2:
        if st.button("🔄 Reset Draft", use_container_width=True):
            for k in [k for k in list(st.session_state.keys()) if k.startswith("q_mcq_")]:
                st.session_state.pop(k, None)
            st.session_state.questions = []; st.session_state.results = None
            st.session_state.current_quiz_id = None
            st.session_state.llm_calls = 0; st.session_state.llm_cost = 0.0
            st.session_state.last_build_calls = 0; st.session_state.last_build_cost = 0.0
            st.session_state.last_questions = 0; st.session_state.build_time = 0.0
            get_llm.clear(); st.rerun()

    if st.session_state.questions:
        total_mins_preview = int(st.session_state.get("prof_total_time_min") or max(2, int(round(2 * len(st.session_state.questions)))))
        per_q_preview = total_mins_preview / max(1, len(st.session_state.questions))
        st.info(
            f"Built in **{st.session_state.get('build_time',0.0):.2f} sec** | "
            f"LLM calls: **{st.session_state.get('llm_calls', 0)}** | "
            f"Est. cost: **${st.session_state.get('llm_cost', 0.0):.4f}** | "
            f"Questions: **{len(st.session_state.questions)}**  | "
            f"⏳ Timer: total {total_mins_preview} min (≈ {per_q_preview:.2f} min/Q)"
        )
        with st.expander("Preview (answers visible to professor)", expanded=True):
            for i, q in enumerate(st.session_state.questions):
                st.markdown(f"**Q{i+1}. {q['question']}**")
                st.write({chr(65+j): opt for j, opt in enumerate(q["options"])})
                st.write(f"✅ Correct: {chr(65+q['answer_index'])}")
                st.caption(f"Explanation: {q.get('explanation','')}")

        st.subheader("Publish")
        title = st.text_input("Quiz title", "Untitled Quiz")
        if st.button("📢 Publish quiz", type="primary"):
            if not st.session_state.questions:
                st.warning("Build a quiz first.")
            else:
                store = _load_store()
                quiz_id = str(uuid.uuid4()); code = _gen_quiz_code()
                student_qs = [{"id": q["id"], "question": q["question"], "options": q["options"]} for q in st.session_state.questions]
                key  = {q["id"]: q["answer_index"] for q in st.session_state.questions}
                exps = {q["id"]: q.get("explanation","") for q in st.session_state.questions}
                chosen_total_min = int(st.session_state.get("prof_total_time_min") or max(2, int(round(2 * len(student_qs)))))
                
                # Fetching parameters exactly as they were available in the sidebar
                difficulty = st.session_state.get("prof_difficulty", "medium")
                show_exps = st.session_state.get("prof_show_explanations_to_students", True)
                shuffle_choices = st.session_state.get("prof_shuffle_choices", True)

                store["quizzes"][quiz_id] = {
                    "quiz_id": quiz_id, "title": title, "code": code, "owner": "prof",
                    "settings": {
                        "difficulty": difficulty,
                        "num_questions": len(student_qs),
                        "show_explanations": bool(show_exps),
                        "shuffle_choices": bool(shuffle_choices),
                        "total_time_sec": int(60 * chosen_total_min),
                        "time_per_question_min": float(chosen_total_min / max(1, len(student_qs))),
                    },
                    "student_questions": student_qs,
                    "answer_key": key,
                    "explanations": exps,
                    "created_at": time.time(),
                    "status": "published",
                }
                _save_store(store)
                st.success(f"Published ✅  | Quiz Code: **{code}**")
                st.session_state.current_quiz_id = quiz_id

    # ============================ Agent 5 — Store (dashboard) ============================
    st.header("Dashboard")
    store = _load_store()
    if not store["quizzes"]:
        st.info("No published quizzes yet.")
    else:
        for qid, qrec in list(store["quizzes"].items()):
            attempts = [a for a in store["attempts"] if a["quiz_id"] == qid]
            with st.expander(f"{qrec['title']} — Code: {qrec['code']}  | Attempts: {len(attempts)}", expanded=False):
                st.write("Settings:", qrec["settings"])
                with st.form(f"update_{qid}"):
                    current_exps = bool(qrec.get("settings", {}).get("show_explanations", False))
                    new_exps = st.toggle("Show explanations to students", current_exps)
                    save = st.form_submit_button("Save settings")
                if save:
                    store = _load_store()
                    if qid in store["quizzes"]:
                        store["quizzes"][qid]["settings"]["show_explanations"] = bool(new_exps)
                        _save_store(store); st.success("Settings updated."); st.rerun()
                if attempts:
                    rows = [
                        {
                            "student_name": a.get("student_name",""),
                            "email": a.get("student_email",""),
                            "score": a["score"], "total": a["total"],
                            "time_taken": _fmt_mmss(a.get("time_taken_sec", 0)),
                            "time_left":  _fmt_mmss(a.get("time_left_sec", 0)),
                            "auto": "Yes" if a.get("auto_submitted") else "No",
                            "submitted_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(a.get("submitted_at", 0)))
                        }
                        for a in attempts
                    ]
                    st.dataframe(rows, hide_index=True)
                else:
                    st.caption("No attempts yet.")
