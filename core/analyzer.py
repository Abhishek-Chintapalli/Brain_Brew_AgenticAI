import uuid
import json
import textwrap
import string
from dataclasses import dataclass
from typing import List, Dict, Literal, Optional
from .llm import LLMInterface

@dataclass
class AnalysisConfig:
    num_questions: int = 10
    difficulty: Literal["easy","medium","hard"] = "medium"

_punc_tbl = str.maketrans('', '', string.punctuation)
def _norm(s: str) -> str: return " ".join(s.lower().translate(_punc_tbl).split())

def _dedup_questions(qs: List[Dict]) -> List[Dict]:
    seen = set(); uniq = []
    for q in qs:
        key = _norm(q["question"])
        if key in seen: continue
        opts_norm = tuple(_norm(o) for o in q["options"])
        if len(set(opts_norm)) < 4: continue
        seen.add(key); uniq.append(q)
    return uniq

class ContentAnalyzer:
    def __init__(self, llm: LLMInterface): self.llm = llm

    def _difficulty_prompt(self, diff: str) -> str:
        if diff=="easy":  return "EASY: focus on definitions/basic facts; clear distractors."
        if diff=="hard":  return "HARD: multi-step reasoning/calculation; subtle distractors."
        return "MEDIUM: mix application + short reasoning; plausible distractors."

    def _temp(self, diff: str) -> float:
        return {"easy":0.15,"medium":0.2,"hard":0.25}.get(diff,0.2)

    def _parse(self, qs: List[Dict]) -> List[Dict]:
        out=[]
        for q in qs:
            try:
                opts=q.get("options",[]); ai=int(q.get("answer_index",0))
                if not isinstance(opts,list) or len(opts)!=4: continue
                if ai<0 or ai>3: continue
                out.append({
                    "id": q.get("id") or str(uuid.uuid4()),
                    "type":"mcq","question":str(q["question"]),
                    "options":[str(o) for o in opts],
                    "answer_index":ai,"explanation":str(q.get("explanation",""))
                })
            except Exception: continue
        return out

    def generate_mcqs(self, top_chunks: List[str], cfgA: AnalysisConfig,
                      extra: Optional[Dict]=None, enforce_exact: bool=False) -> Dict:
        extra = extra or {}
        limited = "\n\n".join(textwrap.shorten(c, width=700) for c in top_chunks[:8])
        sys = (
            "You are a precise quiz generator. Return STRICT JSON with key 'questions' (list). "
            "Only MCQs based ONLY on the provided context. "
            "Each item: {type:'mcq', question, options[4], answer_index(0-3), explanation}. "
            f"{self._difficulty_prompt(cfgA.difficulty)} Output EXACTLY the requested number. "
            "Avoid reusing the same question wording."
        )
        user = json.dumps({"context": limited, "num_questions": cfgA.num_questions,
                           "difficulty": cfgA.difficulty, **extra}, ensure_ascii=False)
        temp = self._temp(cfgA.difficulty)

        out = self.llm.chat_json(sys, user, temperature=temp)
        valid = _dedup_questions(self._parse(out.get("questions", [])))

        if enforce_exact and self.llm.enabled and len(valid) != cfgA.num_questions:
            banned = [q["question"] for q in valid]
            sys2 = sys + " IMPORTANT: produce EXACTLY 'num_questions' MCQs. Do not repeat: " + "; ".join(banned[:20])
            out2 = self.llm.chat_json(sys2, user, temperature=temp)
            valid = _dedup_questions(valid + self._parse(out2.get("questions", [])))

        if len(valid)>cfgA.num_questions: valid=valid[:cfgA.num_questions]
        while len(valid)<cfgA.num_questions:
            base = valid or [{
                "id": str(uuid.uuid4()), "type":"mcq", "question":"Which structure is LIFO?",
                "options":["Queue","Stack","Array","Heap"], "answer_index":1, "explanation":"Stacks are LIFO."
            }]
            i = len(valid); item = dict(base[i % len(base)]); item["id"] = str(uuid.uuid4())
            item["question"] = f"{item['question']} (variant {i+1})"
            valid.append(item)
        return {"questions": valid}
