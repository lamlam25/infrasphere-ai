"""Retrieval engine for the Knowledge Grid."""
from __future__ import annotations

import logging
import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RetrievalEngine:
    """
    Retrieves relevant chunks for a user query using:
      1. Dense vector search (Qdrant)
      2. Optional keyword boost (TF overlap)
      3. Optional document-permission filter
      4. Combined reranking
    """

    def __init__(self, embedding_provider=None, vector_store=None):
        from .embeddings import MockEmbeddingProvider

        self.embedder = embedding_provider or MockEmbeddingProvider()
        self.vector_store = vector_store

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns top_k chunks ranked by combined vector + keyword score.
        """
        if not self.vector_store:
            logger.warning("No vector store configured; returning empty results")
            return []

        # 1. Embed query
        query_vector = self.embedder.embed_query(query)

        # 2. Vector search — over-fetch to allow reranking
        fetch_k = min(top_k * 4, 50)
        filters: Optional[Dict] = None
        if document_ids and len(document_ids) == 1:
            filters = {"document_id": document_ids[0]}

        candidates = self.vector_store.search(query_vector, top_k=fetch_k, filters=filters)

        # 3. Apply multi-document filter (when >1 doc specified)
        if document_ids and len(document_ids) > 1:
            candidates = [c for c in candidates if c.get("document_id") in set(document_ids)]

        # 4. Document permission filter (placeholder — integrate with auth layer)
        if user_id:
            candidates = self._apply_permission_filter(candidates, user_id)

        # 5. Rerank
        ranked = self._rerank(candidates, query)

        return ranked[:top_k]

    # ------------------------------------------------------------------
    # Keyword scoring
    # ------------------------------------------------------------------

    def _keyword_score(self, query: str, content: str) -> float:
        """Simple TF-based keyword overlap score (0–1)."""
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return 0.0
        content_tokens = self._tokenize(content)
        content_tf = Counter(content_tokens)
        content_total = max(len(content_tokens), 1)

        score = 0.0
        for token in set(query_tokens):
            tf = content_tf.get(token, 0) / content_total
            # log-normalise TF to dampen very frequent tokens
            score += math.log1p(tf * 100)
        return score / len(set(query_tokens))

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z\u0980-\u09FF]{2,}\b", text.lower())

    # ------------------------------------------------------------------
    # Reranking
    # ------------------------------------------------------------------

    def _rerank(self, candidates: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Combine vector score + keyword score, normalise, sort descending."""
        if not candidates:
            return []

        # Annotate with keyword scores
        for c in candidates:
            c["keyword_score"] = self._keyword_score(query, c.get("content", ""))

        # Normalise vector scores (already cosine 0–1 from Qdrant)
        max_vs = max(c["score"] for c in candidates) or 1.0
        max_ks = max(c["keyword_score"] for c in candidates) or 1.0

        for c in candidates:
            vs_norm = c["score"] / max_vs
            ks_norm = c["keyword_score"] / max_ks
            # Weight: 70% vector, 30% keyword
            c["combined_score"] = 0.7 * vs_norm + 0.3 * ks_norm

        candidates.sort(key=lambda x: -x["combined_score"])
        return candidates

    # ------------------------------------------------------------------
    # Permission filter (stub — replace with real auth checks)
    # ------------------------------------------------------------------

    def _apply_permission_filter(
        self, candidates: List[Dict[str, Any]], user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Placeholder: in production, check document visibility vs user role.
        Currently passes all candidates through.
        """
        return candidates
