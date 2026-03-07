import io
import re
import collections
import streamlit as st
import config as cfg
from typing import List, Dict

try:
    import numpy as np  # noqa: F401
    from sentence_transformers import SentenceTransformer
    from pypdf import PdfReader
    HAVE_RAG = True
except Exception:
    HAVE_RAG = False
    st.warning("Some RAG packages are missing. Run: pip install pypdf sentence-transformers")

def read_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    return "\n".join((page.extract_text() or "") for page in reader.pages)

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> List[str]:
    words = text.split()
    out, i = [], 0
    while i < len(words):
        out.append(" ".join(words[i:i+chunk_size]))
        i += chunk_size - overlap
    return [c.strip() for c in out if c.strip()]

def extract_keywords(text: str, top_k: int = 8) -> List[str]:
    stop = set("""
    the a an and or of to in for on at by from with as is are was were be being been that this those these
    it its they their them he she his her we our you your i me my mine not no if then else when while into
    about over under between within without above below up down out very more most less least also may can
    will should could would than such other same different using use used based include includes including
    """.split())
    tokens = [re.sub(r"[^a-z0-9\-]+", "", w.lower()) for w in re.findall(r"[A-Za-z0-9\-]+", text)]
    tokens = [t for t in tokens if t and t not in stop and not t.isdigit() and len(t) > 2]
    freq = collections.Counter(tokens)
    return [w for w, _ in freq.most_common(top_k)]

class VectorStore:
    def __init__(self, model_name: str = cfg.RAG_EMBED_MODEL):
        self.model_name = model_name
        self.embedder = None
        self.chunks: List[str] = []
        self.embeddings = None

    def _ensure(self):
        if self.embedder is None:
            self.embedder = SentenceTransformer(self.model_name)

    def build(self, chunks: List[str]):
        self._ensure()
        self.chunks = chunks
        self.embeddings = self.embedder.encode(chunks, convert_to_tensor=True, normalize_embeddings=True)

    def search(self, query: str, k: int = 8) -> List[str]:
        if self.embeddings is None or len(self.chunks) == 0:
            return []
            
        self._ensure()
        q_emb = self.embedder.encode(query, convert_to_tensor=True, normalize_embeddings=True)
        
        import torch
        # Cosine similarity (dot product of normalized vectors)
        cos_scores = torch.mm(q_emb.unsqueeze(0), self.embeddings.transpose(0, 1))[0]
        
        # Get top k indices
        top_k = min(k, len(self.chunks))
        top_results = torch.topk(cos_scores, k=top_k)
        
        return [self.chunks[idx] for idx in top_results.indices.tolist()]

class DocumentProcessor:
    def __init__(self): 
        self.vstore = VectorStore() if HAVE_RAG else None
        
    def process(self, uploaded_file) -> Dict:
        if uploaded_file is None:
            return {"success": False, "error": "No file uploaded."}
        filename = getattr(uploaded_file, "name", "uploaded").lower()
        raw = uploaded_file.read()
        is_pdf = filename.endswith(".pdf") or (isinstance(raw,(bytes,bytearray)) and raw[:5]==b"%PDF-")
        text = read_pdf(raw) if is_pdf else raw.decode("utf-8", errors="ignore")
        text = re.sub(r"\s+\n", "\n", text)
        chunks = chunk_text(text)
        if not chunks:
            return {"success": False, "error": "No text found in document."}
        if self.vstore:
            try: self.vstore.build(chunks)
            except Exception: self.vstore = None
        return {"success": True, "chunks": chunks, "text": text, "total_chars": len(text)}
