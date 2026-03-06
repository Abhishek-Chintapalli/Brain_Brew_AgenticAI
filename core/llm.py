from typing import Optional
import json
import requests
import streamlit as st
import config as cfg

class LLMInterface:
    def __init__(self, model: str = cfg.MODEL_NAME, api_key: Optional[str] = None):
        key = api_key or cfg.get_api_key()
        self.enabled = bool(key)
        self.api_key = key
        self.model = model
        self.call_count = 0
        self.cost_per_call = cfg.COST_PER_CALL

    def _post(self, system: str, user: str, temperature: float) -> dict:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "temperature": temperature,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {"type": "json_object"},
            "max_tokens": cfg.MAX_TOKENS,
        }
        self.call_count += 1
        resp = requests.post(cfg.CHAT_URL, headers=headers, json=payload, timeout=90)
        resp.raise_for_status()
        data = resp.json()
        raw = data["choices"][0]["message"]["content"]
        try:
            return json.loads(raw)
        except Exception:
            if "}" in raw:
                fixed = raw[: raw.rfind("}") + 1]
                return json.loads(fixed)
            raise

    def chat_json(self, system: str, user: str, temperature: float = 0.2) -> dict:
        if not self.enabled:
            # Demo fallback: local stub returning exactly N questions
            try:
                req = json.loads(user); n = int(req.get("num_questions", 10))
            except Exception:
                n = 10
            return {"questions":[{
                "type":"mcq",
                "question": f"Which structure is LIFO? (demo {i+1})",
                "options":["Queue","Stack","Array","Heap"],
                "answer_index":1,
                "explanation":"Stacks are Last-In, First-Out."
            } for i in range(n)]}
        return self._post(system, user, temperature)

    @property
    def estimated_cost(self) -> float:
        return round(self.call_count * self.cost_per_call, 4)

@st.cache_resource
def get_llm(api_key: str, model: str = cfg.MODEL_NAME) -> LLMInterface:
    return LLMInterface(model=model, api_key=api_key)
