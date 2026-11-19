"""RAG Answer Generator for the Knowledge Grid."""
from __future__ import annotations

import logging
import os
import textwrap
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_MOCK_MODE_LABEL = "[MOCK_MODE]"
_MAX_CONTEXT_CHARS = 3000
_MIN_CHUNKS_FOR_GROUNDED = 1
_MIN_SCORE_THRESHOLD = 0.05


class RAGAnswerGenerator:
    """
    Generates answers from retrieved chunks.

    When an LLM is configured it will call it; otherwise it falls back to a
    deterministic mock that extracts key sentences from the top chunks.
    All mock answers are clearly labelled with MOCK_MODE.
    """

    def __init__(self, llm_provider: str = "mock", llm_config: Optional[Dict] = None):
        self.llm_provider = llm_provider
        self.llm_config = llm_config or {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        question: str,
        chunks: List[Dict[str, Any]],
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Returns:
            {
              query, answer, language, answer_status,
              sources: [{document_id, document_title, page, chunk_id, excerpt}],
              limitations, generation_mode
            }

        answer_status:
            grounded               — answer fully supported by retrieved chunks
            partially_grounded     — answer uses some but not all retrieved chunks
            insufficient_evidence  — no useful chunks found
            generation_failed      — LLM/mock raised an exception
        """
        # Build sources from chunks (only use ones above threshold)
        usable_chunks = [
            c for c in chunks if c.get("score", c.get("combined_score", 1.0)) >= _MIN_SCORE_THRESHOLD
        ]

        sources = self._build_sources(usable_chunks)

        if not usable_chunks:
            return {
                "query": question,
                "answer": (
                    "I could not find sufficient information in the knowledge base to answer this question. "
                    "Please consult domain experts or upload relevant documents."
                ),
                "language": language,
                "answer_status": "insufficient_evidence",
                "sources": [],
                "limitations": ["No relevant documents found in the knowledge base."],
                "generation_mode": "abstention",
            }

        try:
            if self.llm_provider != "mock":
                answer = self._llm_answer(question, usable_chunks, language)
                generation_mode = self.llm_provider
            else:
                answer = self._mock_answer(question, usable_chunks)
                generation_mode = f"mock {_MOCK_MODE_LABEL}"

            answer_status = (
                "grounded"
                if len(usable_chunks) >= _MIN_CHUNKS_FOR_GROUNDED
                else "partially_grounded"
            )
        except Exception as exc:
            logger.error("Answer generation failed: %s", exc)
            return {
                "query": question,
                "answer": f"Answer generation failed: {exc}",
                "language": language,
                "answer_status": "generation_failed",
                "sources": sources,
                "limitations": [str(exc)],
                "generation_mode": "failed",
            }

        limitations: List[str] = []
        if generation_mode.startswith("mock"):
            limitations.append(
                "This answer was generated in MOCK_MODE without a real language model. "
                "It is derived mechanically from retrieved document excerpts."
            )
        if len(usable_chunks) < 3:
            limitations.append("Answer is based on fewer than 3 retrieved chunks; may be incomplete.")

        return {
            "query": question,
            "answer": answer,
            "language": language,
            "answer_status": answer_status,
            "sources": sources,
            "limitations": limitations,
            "generation_mode": generation_mode,
        }

    # ------------------------------------------------------------------
    # Context builder
    # ------------------------------------------------------------------

    def _build_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Concatenate chunk contents, truncated to _MAX_CONTEXT_CHARS."""
        parts = []
        total = 0
        for i, c in enumerate(chunks, start=1):
            snippet = c.get("content", "").strip()
            prefix = f"[Excerpt {i}]"
            entry = f"{prefix}\n{snippet}"
            if total + len(entry) > _MAX_CONTEXT_CHARS:
                remaining = _MAX_CONTEXT_CHARS - total
                if remaining > 50:
                    parts.append(entry[:remaining] + "…")
                break
            parts.append(entry)
            total += len(entry)
        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Mock answer (no LLM)
    # ------------------------------------------------------------------

    def _mock_answer(self, question: str, chunks: List[Dict[str, Any]]) -> str:
        """
        Deterministic answer assembled from top chunk sentences.
        Clearly marked as MOCK_MODE — never invents citations.
        """
        import re

        def top_sentences(text: str, n: int = 3) -> List[str]:
            q_words = set(re.findall(r"\b\w{3,}\b", question.lower()))
            sentences = re.split(r"(?<=[.!?])\s+", text)
            scored = []
            for s in sentences:
                s = s.strip()
                if len(s) < 20:
                    continue
                s_words = set(re.findall(r"\b\w{3,}\b", s.lower()))
                overlap = len(q_words & s_words)
                scored.append((overlap, s))
            scored.sort(key=lambda x: -x[0])
            return [s for _, s in scored[:n]]

        answer_parts: List[str] = [f"{_MOCK_MODE_LABEL} (No LLM configured — answer extracted mechanically)\n"]

        for i, chunk in enumerate(chunks[:3], start=1):
            sentences = top_sentences(chunk.get("content", ""), n=2)
            if sentences:
                answer_parts.append(f"Based on Excerpt {i}: " + " ".join(sentences))

        if len(answer_parts) == 1:
            answer_parts.append("No specific sentences matched the query in the retrieved excerpts.")

        return "\n\n".join(answer_parts)

    # ------------------------------------------------------------------
    # LLM answer (stub — replace with real provider)
    # ------------------------------------------------------------------

    def _llm_answer(self, question: str, chunks: List[Dict[str, Any]], language: str) -> str:
        context = self._build_context(chunks)
        from app.config import get_settings
        settings = get_settings()
        api_key = settings.llm_api_key

        if settings.llm_provider in ("gemini", "openai_compatible") and api_key:
            try:
                import httpx
                model_name = settings.llm_model or "gemini-flash-latest"
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                prompt = (
                    f"You are InfraSphere AI Knowledge Grid expert.\n"
                    f"Answer the question using ONLY the provided operational document excerpts.\n"
                    f"Cite documents like [DOC-FLD-01 p.1].\n\n"
                    f"EXCERPTS:\n{context}\n\n"
                    f"QUESTION: {question}\n\n"
                    f"LANGUAGE: {'Bengali' if language == 'bn' else 'English'}\n\n"
                    f"ANSWER:"
                )
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                res = httpx.post(url, json=payload, timeout=20.0)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
            except Exception as e:
                logger.warning(f"Live Gemini answer generation error: {e}, falling back to extracted sentences")

        return self._mock_answer(question, chunks)

    # ------------------------------------------------------------------
    # Sources builder
    # ------------------------------------------------------------------

    @staticmethod
    def _build_sources(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sources = []
        for c in chunks:
            meta = c.get("metadata", {})
            sources.append(
                {
                    "document_id": c.get("document_id"),
                    "document_title": meta.get("title", meta.get("file_path", "Unknown")),
                    "page": meta.get("page_number", c.get("page_number", 1)),
                    "chunk_id": c.get("chunk_id"),
                    "excerpt": textwrap.shorten(c.get("content", ""), width=200, placeholder="…"),
                }
            )
        return sources
