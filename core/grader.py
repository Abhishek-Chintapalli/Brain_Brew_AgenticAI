import streamlit as st
import re
from typing import List, Dict

def grade_current_answers(questions: List[Dict]) -> Dict:
    unanswered = [i+1 for i in range(len(questions)) if st.session_state.get(f"q_mcq_{i}", None) is None]
    if unanswered:
        raise ValueError(f"Please answer all questions: {unanswered}")
    correct = 0; details=[]
    for i, q in enumerate(questions):
        sel = int(st.session_state.get(f"q_mcq_{i}"))
        ans = q["answer_index"]; ok = (sel == ans); correct += int(ok)
        details.append({"q": i+1, "qid": q["id"], "selected": sel, "correct": ans,
                        "is_correct": ok, "explanation": q.get("explanation","")})
    return {"score": correct, "total": len(questions), "details": details}

def analyze_results(grade: Dict) -> Dict:
    pct = 0 if grade["total"]==0 else round(100*grade["score"]/grade["total"], 2)
    missed, plan = [], []
    for d in grade["details"]:
        if not d["is_correct"] and d["explanation"]:
            token = re.findall(r"[A-Za-z]{4,}", d["explanation"])
            if token: missed.append(token[0].lower())
    for t in sorted(set(missed))[:3]:
        plan.append(f"Review concept: **{t}** — make 3 flashcards and reattempt 5 MCQs.")
    return {"percentage": pct, "study_plan": plan}
