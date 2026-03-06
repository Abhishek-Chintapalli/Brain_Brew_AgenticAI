import time
import uuid
import streamlit as st

from core.storage import _load_store, _save_store
from core.grader import grade_current_answers, analyze_results
from utils.helpers import _fmt_mmss, tick_every
from ui.components import render_quiz_mcq

def render_student():
    st.subheader("Join Quiz")
    with st.form("student_join"):
        name = st.text_input("Name")
        email = st.text_input("Email (optional)")
        code = st.text_input("Quiz Code")
        submitted = st.form_submit_button("Start")

    if submitted:
        if not name.strip() or not code.strip():
            st.error("Please enter both **Name** and **Quiz Code** to start.")
            st.session_state.student_ready = False
        else:
            quiz = None
            for qid, qrec in _load_store()["quizzes"].items():
                if qrec["code"].strip().upper() == code.strip().upper() and qrec["status"] == "published":
                    quiz = qrec; break
            if quiz is None:
                st.error("Invalid quiz code."); st.session_state.student_ready = False
            else:
                st.session_state.current_quiz_id = quiz["quiz_id"]
                merged = []
                key = quiz["answer_key"]; exps = quiz.get("explanations", {})
                for item in quiz["student_questions"]:
                    merged.append({
                        "id": item["id"], "type": "mcq",
                        "question": item["question"], "options": item["options"],
                        "answer_index": key.get(item["id"], 0), "explanation": exps.get(item["id"], "")
                    })
                for k in [k for k in list(st.session_state.keys()) if k.startswith("q_mcq_")]:
                    st.session_state.pop(k, None)

                st.session_state.questions = merged
                st.session_state.results = None
                st.session_state.student_ready = True

                total_sec = int(quiz["settings"].get("total_time_sec", 2 * 60 * len(merged)))
                st.session_state.total_time_sec = total_sec
                if not st.session_state.get("quiz_end_ts"):
                    st.session_state.quiz_end_ts = time.time() + total_sec
                if not st.session_state.get("quiz_start_ts"):
                    st.session_state.quiz_start_ts = time.time()
                st.session_state.auto_submitted = False
                
                # Persist name and email to session state for the submission block
                st.session_state.student_name = name
                st.session_state.student_email = email

                st.success(f"Loaded quiz: {quiz['title']} ({len(merged)} questions)")

    if st.session_state.student_ready and st.session_state.questions:
        # Timer UI
        total_sec = int(st.session_state.get("total_time_sec", 0)) or (2 * 60 * len(st.session_state.questions))
        end_ts = st.session_state.get("quiz_end_ts") or (time.time() + total_sec)
        remaining = int(end_ts - time.time())

        col_t1, col_t2 = st.columns([1, 5])
        with col_t1:
            st.metric("Time left", _fmt_mmss(remaining))
        with col_t2:
            pct = 0.0 if total_sec <= 0 else max(0.0, min(1.0, remaining / total_sec))
            st.progress(pct, text="Timer")

        tick_every(1000, "student_timer_tick")

        name = st.session_state.get("student_name", "Student")
        email = st.session_state.get("student_email", "")

        # Auto-submit when time expires
        if remaining <= 0 and not st.session_state.get("auto_submitted", False):
            try:
                grade = grade_current_answers(st.session_state.questions)
            except Exception:
                grade = {"score": 0, "total": len(st.session_state.questions), "details": []}
                for i, q in enumerate(st.session_state.questions):
                    sel = st.session_state.get(f"q_mcq_{i}", None)
                    ok = (sel is not None and int(sel) == q["answer_index"])
                    if ok: grade["score"] += 1
                    grade["details"].append({
                        "q": i+1, "qid": q["id"],
                        "selected": (-1 if sel is None else int(sel)),
                        "correct": q["answer_index"], "is_correct": ok,
                        "explanation": q.get("explanation","")
                    })

            stats = analyze_results(grade)
            st.session_state.results = {"grade": grade, "stats": stats}
            st.session_state.auto_submitted = True

            start_ts = st.session_state.get("quiz_start_ts") or (end_ts - total_sec)
            submit_ts = time.time()
            time_taken_sec = max(0, int(submit_ts - start_ts))
            time_left_sec  = max(0, int(end_ts - submit_ts))

            store = _load_store()
            store["attempts"].append({
                "attempt_id": str(uuid.uuid4()),
                "quiz_id": st.session_state.current_quiz_id,
                "student_name": name, "student_email": email,
                "answers": [{"qid": d["qid"], "selected": d["selected"]} for d in grade["details"]],
                "score": grade["score"], "total": grade["total"],
                "started_at": start_ts, "submitted_at": submit_ts,
                "time_taken_sec": time_taken_sec, "time_left_sec": time_left_sec,
                "auto_submitted": True,
            })
            _save_store(store)

        locked = (remaining <= 0) or bool(st.session_state.get("auto_submitted")) or bool(st.session_state.get("results"))
        render_quiz_mcq(st.session_state.questions, disable=locked)

        if (not locked) and st.button("✅ Submit answers", type="primary", use_container_width=True):
            try:
                grade = grade_current_answers(st.session_state.questions)
                stats = analyze_results(grade)
                st.session_state.results = {"grade": grade, "stats": stats}

                start_ts = st.session_state.get("quiz_start_ts") or (end_ts - total_sec)
                submit_ts = time.time()
                time_taken_sec = max(0, int(submit_ts - start_ts))
                time_left_sec  = max(0, int(end_ts - submit_ts))

                store = _load_store()
                store["attempts"].append({
                    "attempt_id": str(uuid.uuid4()),
                    "quiz_id": st.session_state.current_quiz_id,
                    "student_name": name, "student_email": email,
                    "answers": [{"qid": d["qid"], "selected": d["selected"]} for d in grade["details"]],
                    "score": grade["score"], "total": grade["total"],
                    "started_at": start_ts, "submitted_at": submit_ts,
                    "time_taken_sec": time_taken_sec, "time_left_sec": time_left_sec,
                    "auto_submitted": False,
                })
                _save_store(store)
            except ValueError as ve:
                st.error(str(ve))

    # Results (respect instructor visibility)
    if st.session_state.student_ready and st.session_state.results:
        qrec = _load_store()["quizzes"].get(st.session_state.current_quiz_id)
        allow_exps = False
        if qrec and isinstance(qrec.get("settings"), dict):
            allow_exps = bool(qrec["settings"].get("show_explanations", False))

        grade = st.session_state.results["grade"]; stats = st.session_state.results["stats"]
        st.markdown("---"); st.subheader("✅ Results")
        st.write(f"Score: **{grade['score']} / {grade['total']}**  |  Percentage: **{stats['percentage']}%**")

        start_ts = st.session_state.get("quiz_start_ts")
        if start_ts:
            taken = max(0, int(time.time() - start_ts))
            total_sec = int(st.session_state.get("total_time_sec", 0)) or (2 * 60 * grade["total"])
            st.caption(f"⏱️ Time taken (live): {_fmt_mmss(taken)} / {_fmt_mmss(total_sec)}")

        if allow_exps:
            with st.expander("Answer key & explanations", expanded=True):
                for d in grade["details"]:
                    q_idx = d["q"] - 1
                    opts = st.session_state.questions[q_idx]["options"]
                    your = opts[d['selected']] if d['selected'] >= 0 else "(no answer)"
                    correct = opts[d['correct']]
                    exp_text = st.session_state.questions[q_idx].get("explanation") or "Explanation not provided."
                    st.markdown(
                        f"**Q{d['q']}** — {'✅ Correct' if d['is_correct'] else '❌ Incorrect'}  \n"
                        f"- **Your answer:** {your}  \n"
                        f"- **Correct answer:** {correct}  \n"
                        f"- **Explanation:** {exp_text}"
                    )
        else:
            st.info("Explanations are hidden for this quiz per instructor settings.")
