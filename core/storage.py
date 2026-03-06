from typing import Dict
import os
import json
import random
import config as cfg

def _load_store() -> Dict:
    path = cfg.QUIZ_STORE_PATH
    if not os.path.exists(path):
        return {"quizzes": {}, "attempts": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"quizzes": {}, "attempts": []}

def _save_store(store: Dict):
    path = cfg.QUIZ_STORE_PATH
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)

def _gen_quiz_code(n: int = 6) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(alphabet) for _ in range(n))
