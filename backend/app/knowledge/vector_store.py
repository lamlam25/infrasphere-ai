"""Qdrant vector store wrapper for Knowledge Grid."""
from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        FieldCondition,
        Filter,
        MatchValue,
        PointIdsList,
        PointStruct,
        VectorParams,
    )

    _QDRANT_AVAILABLE = True
except ImportError:
    _QDRANT_AVAILABLE = False
    logger.warning("qdrant-client not installed — VectorStore will use in-memory fallback")


class _InMemoryFallback:
    """Minimal in-memory vector store when qdrant-client is unavailable."""

    def __init__(self, dim: int):
        self.dim = dim
        self.points: List[Dict] = []

    def upsert(self, points):
        for p in points:
            self.points = [x for x in self.points if x["id"] != p["id"]]
            self.points.append(p)

    def search(self, vector, top_k, filters=None):
        import numpy as np

        q = np.array(vector)
        scored = []
        for p in self.points:
            if filters:
                doc_id = filters.get("document_id")
                if doc_id and p["payload"].get("document_id") != doc_id:
                    continue
            v = np.array(p["vector"])
            score = float(np.dot(q, v) / (np.linalg.norm(q) * np.linalg.norm(v) + 1e-9))
            scored.append((score, p))
        scored.sort(key=lambda x: -x[0])
        return scored[:top_k]

    def delete(self, ids):
        self.points = [p for p in self.points if p["id"] not in ids]

    def ids_for_doc(self, document_id):
        return [p["id"] for p in self.points if p["payload"].get("document_id") == document_id]


class VectorStore:
    """Wraps Qdrant client for document storage and retrieval."""

    COLLECTION_NAME = "infrasphere_docs"

    def __init__(self, path: str, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self._fallback: Optional[_InMemoryFallback] = None
        self._client = None

        if _QDRANT_AVAILABLE:
            storage = Path(path)
            storage.mkdir(parents=True, exist_ok=True)
            self._client = QdrantClient(path=str(storage))
            self._ensure_collection()
        else:
            logger.warning("Using in-memory vector store fallback")
            self._fallback = _InMemoryFallback(embedding_dim)

    # ------------------------------------------------------------------
    # Collection management
    # ------------------------------------------------------------------

    def _ensure_collection(self) -> None:
        existing = [c.name for c in self._client.get_collections().collections]
        if self.COLLECTION_NAME not in existing:
            self._client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE),
            )
            logger.info("Created Qdrant collection '%s'", self.COLLECTION_NAME)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def upsert_chunks(self, chunks: List[Dict[str, Any]], document_id: str) -> None:
        """Store chunk embeddings with metadata payload."""
        if not chunks:
            return

        if self._fallback:
            points = [
                {
                    "id": chunk.get("chunk_id", str(uuid.uuid4())),
                    "vector": chunk["embedding"],
                    "payload": {
                        "document_id": document_id,
                        "chunk_index": chunk.get("chunk_index", 0),
                        "content": chunk.get("content", ""),
                        "metadata": chunk.get("metadata", {}),
                    },
                }
                for chunk in chunks
                if "embedding" in chunk
            ]
            self._fallback.upsert(points)
            return

        points = [
            PointStruct(
                id=chunk.get("chunk_id", str(uuid.uuid4())),
                vector=chunk["embedding"],
                payload={
                    "document_id": document_id,
                    "chunk_index": chunk.get("chunk_index", 0),
                    "content": chunk.get("content", ""),
                    "metadata": chunk.get("metadata", {}),
                },
            )
            for chunk in chunks
            if "embedding" in chunk
        ]
        if points:
            self._client.upsert(collection_name=self.COLLECTION_NAME, points=points)
            logger.debug("Upserted %d chunks for document %s", len(points), document_id)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """
        Returns list of:
            {chunk_id, document_id, score, content, metadata}
        """
        if self._fallback:
            raw = self._fallback.search(query_vector, top_k, filters)
            return [
                {
                    "chunk_id": p["id"],
                    "document_id": p["payload"].get("document_id"),
                    "score": score,
                    "content": p["payload"].get("content", ""),
                    "metadata": p["payload"].get("metadata", {}),
                }
                for score, p in raw
            ]

        qdrant_filter = None
        if filters and "document_id" in filters:
            qdrant_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=filters["document_id"]),
                    )
                ]
            )

        results = self._client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )

        return [
            {
                "chunk_id": str(r.id),
                "document_id": r.payload.get("document_id"),
                "score": r.score,
                "content": r.payload.get("content", ""),
                "metadata": r.payload.get("metadata", {}),
            }
            for r in results
        ]

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_document(self, document_id: str) -> None:
        """Remove all chunks for a document."""
        if self._fallback:
            ids = self._fallback.ids_for_doc(document_id)
            self._fallback.delete(ids)
            return

        self._client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
        )
        logger.info("Deleted all chunks for document %s", document_id)

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        try:
            if self._fallback:
                return True
            self._client.get_collections()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("VectorStore health check failed: %s", exc)
            return False
