from dataclasses import dataclass
from functools import lru_cache
from math import sqrt
from pathlib import Path
import re
import unicodedata

from ai.llm import llm_service
from core.config import settings


KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"


@dataclass
class RagChunk:
    source: str
    text: str
    embedding: list[float] | None = None


def _tokenize(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", text.lower())
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    stopwords = {
        "le", "la", "les", "de", "du", "des", "un", "une", "et", "ou", "a", "au", "aux",
        "en", "dans", "sur", "pres", "prÃƒÂ¨s", "pour", "par", "avec", "sans", "ce", "cette",
        "qui", "que", "quoi", "je", "tu", "il", "elle", "nous", "vous", "ils", "elles",
        "the", "and", "or", "of", "for", "to", "in", "on", "near",
    }
    tokens = []
    for token in re.findall(r"[\w']+", normalized, flags=re.UNICODE):
        if token in stopwords or len(token) <= 1:
            continue
        if len(token) > 4 and token.endswith("s"):
            token = token[:-1]
        tokens.append(token)
    return set(tokens)


def _cosine(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))
    if not left_norm or not right_norm:
        return 0.0
    return dot / (left_norm * right_norm)


class RagService:
    def __init__(self, knowledge_dir: Path = KNOWLEDGE_DIR) -> None:
        self.knowledge_dir = knowledge_dir

    def _load_chunks(self) -> list[RagChunk]:
        chunks: list[RagChunk] = []
        for path in sorted(self.knowledge_dir.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            sections = re.split(r"\n(?=#{2,3}\s+)", text)
            for section in sections:
                cleaned = section.strip()
                if cleaned:
                    source = path.relative_to(self.knowledge_dir).as_posix()
                    chunks.append(RagChunk(source=source, text=cleaned))
        return chunks

    @lru_cache(maxsize=1)
    def chunks(self) -> tuple[RagChunk, ...]:
        chunks = self._load_chunks()
        if llm_service.available and chunks:
            try:
                embeddings = llm_service.embed([chunk.text for chunk in chunks])
                for chunk, embedding in zip(chunks, embeddings):
                    chunk.embedding = embedding
            except Exception:
                pass
        return tuple(chunks)

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict[str, str | float]]:
        top_k = top_k or settings.RAG_TOP_K
        chunks = list(self.chunks())
        if not chunks:
            return []

        scored: list[tuple[float, RagChunk]] = []
        query_embedding: list[float] | None = None

        if llm_service.available and any(chunk.embedding for chunk in chunks):
            try:
                embeddings = llm_service.embed([query])
                query_embedding = embeddings[0] if embeddings else None
            except Exception:
                query_embedding = None

        query_tokens = _tokenize(query)
        for chunk in chunks:
            if query_embedding and chunk.embedding:
                score = _cosine(query_embedding, chunk.embedding)
            else:
                chunk_tokens = _tokenize(chunk.text)
                score = len(query_tokens.intersection(chunk_tokens)) / max(len(query_tokens), 1)
            scored.append((score, chunk))

        scored.sort(key=lambda item: (item[0], -len(item[1].text)), reverse=True)
        return [
            {
                "source": chunk.source,
                "score": round(score, 4),
                "text": chunk.text,
            }
            for score, chunk in scored[:top_k]
            if score > 0 or not query_tokens
        ]

    @staticmethod
    def format_context(chunks: list[dict[str, str | float]]) -> str:
        if not chunks:
            return "Aucun contexte RAG disponible."
        return "\n\n".join(
            f"Source: {chunk['source']} | score={chunk['score']}\n{chunk['text']}"
            for chunk in chunks
        )


rag_service = RagService()



