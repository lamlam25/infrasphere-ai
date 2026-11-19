"""Document ingestion pipeline for the Knowledge Grid."""
from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


def _normalize_text(text: str) -> str:
    """Clean excess whitespace and fix encoding artifacts."""
    text = unicodedata.normalize("NFKC", text)
    # Collapse runs of whitespace (excluding newlines)
    text = re.sub(r"[^\S\n]+", " ", text)
    # Collapse 3+ consecutive newlines to two
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _detect_language(text: str) -> str:
    """Very lightweight language detection: 'bn' if Bengali chars present, else 'en'."""
    bengali_chars = sum(1 for c in text if "\u0980" <= c <= "\u09FF")
    return "bn" if bengali_chars / max(len(text), 1) > 0.1 else "en"


class DocumentIngestionService:
    """
    Orchestrates the full document ingestion pipeline:
      validate → deduplicate → extract → normalize → chunk → embed → store
    """

    def __init__(
        self,
        chunker=None,
        embedding_provider=None,
        vector_store=None,
        db=None,
    ):
        from .chunking import TextChunker
        from .embeddings import MockEmbeddingProvider

        self.chunker = chunker or TextChunker()
        self.embedder = embedding_provider or MockEmbeddingProvider()
        self.vector_store = vector_store  # optional; skip Qdrant if None
        self.db = db  # optional SQLAlchemy session
        self._seen_hashes: Dict[str, str] = {}  # hash → doc_id (in-memory dedup)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest(self, file_path: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Returns {doc_id, chunk_count, status, file_hash}.

        Pipeline:
        1. Validate extension
        2. Check file hash for deduplication
        3. Extract text
        4. Normalize text
        5. Enrich metadata (language, word count)
        6. Chunk text
        7. Generate embeddings
        8. Store in Qdrant
        9. Save record in DB (if db provided)
        """
        metadata = metadata or {}
        path = Path(file_path)

        # 1. Validate extension
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            return {
                "doc_id": None,
                "chunk_count": 0,
                "status": "failed",
                "error": f"Unsupported file type: {ext}. Supported: {SUPPORTED_EXTENSIONS}",
            }

        # 2. File hash / deduplication
        file_hash = self._hash_file(file_path)
        if file_hash in self._seen_hashes:
            existing_id = self._seen_hashes[file_hash]
            logger.info("Duplicate document detected (hash=%s), existing id=%s", file_hash, existing_id)
            return {
                "doc_id": existing_id,
                "chunk_count": 0,
                "status": "duplicate",
                "file_hash": file_hash,
            }

        # 3. Extract text
        try:
            if ext == ".pdf":
                pages = self._extract_text_pdf(file_path)
            else:
                pages = self._extract_text_plain(file_path)
        except Exception as exc:
            logger.error("Text extraction failed for %s: %s", file_path, exc)
            return {"doc_id": None, "chunk_count": 0, "status": "failed", "error": str(exc)}

        full_text = "\n\n".join(p["text"] for p in pages)

        # 4. Normalize
        full_text = _normalize_text(full_text)

        # 5. Enrich metadata
        language = _detect_language(full_text)
        word_count = len(full_text.split())
        enriched_meta = {
            **metadata,
            "language": language,
            "word_count": word_count,
            "file_path": str(file_path),
            "file_type": ext.lstrip("."),
            "page_count": len(pages),
        }

        # 6. Chunk
        chunks = self.chunker.chunk(full_text, enriched_meta)

        # Assign chunk IDs and page numbers
        for i, chunk in enumerate(chunks):
            chunk["chunk_id"] = f"CHUNK-{uuid.uuid4().hex[:8].upper()}"
            # Approximate page assignment from char_start
            chunk["page_number"] = self._page_for_offset(pages, chunk["char_start"])

        # 7. Generate embeddings
        texts = [c["content"] for c in chunks]
        embeddings = self.embedder.embed_documents(texts) if texts else []
        for chunk, emb in zip(chunks, embeddings):
            chunk["embedding"] = emb

        # 8. Store in vector store
        doc_id = metadata.get("doc_id") or f"DOC-{uuid.uuid4().hex[:8].upper()}"
        if self.vector_store and chunks:
            try:
                self.vector_store.upsert_chunks(chunks, doc_id)
            except Exception as exc:
                logger.error("Vector store upsert failed: %s", exc)

        # 9. Save to DB
        if self.db:
            self._save_to_db(doc_id, file_hash, chunks, enriched_meta)

        # Remember hash
        self._seen_hashes[file_hash] = doc_id

        return {
            "doc_id": doc_id,
            "chunk_count": len(chunks),
            "status": "indexed",
            "file_hash": file_hash,
            "language": language,
            "word_count": word_count,
        }

    # ------------------------------------------------------------------
    # Text extraction
    # ------------------------------------------------------------------

    def _extract_text_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Returns [{page_num, text}] using pymupdf (fitz)."""
        try:
            import fitz  # PyMuPDF
        except ImportError as exc:
            raise ImportError("pymupdf is required for PDF extraction: pip install pymupdf") from exc

        pages = []
        with fitz.open(file_path) as doc:
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text")
                pages.append({"page_num": page_num, "text": text})
        return pages

    def _extract_text_plain(self, file_path: str) -> List[Dict[str, Any]]:
        """Returns [{page_num: 1, text}] for plain text / markdown files."""
        with open(file_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
        return [{"page_num": 1, "text": content}]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _hash_file(file_path: str) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(65536), b""):
                h.update(block)
        return h.hexdigest()

    @staticmethod
    def _page_for_offset(pages: List[Dict], char_start: int) -> int:
        """Return 1-based page number for a character offset in the concatenated text."""
        running = 0
        for p in pages:
            running += len(p["text"]) + 2  # +2 for \n\n separator
            if char_start < running:
                return p["page_num"]
        return pages[-1]["page_num"] if pages else 1

    def _save_to_db(self, doc_id: str, file_hash: str, chunks: List[Dict], meta: Dict) -> None:
        """Persist document record and chunks to SQLite via SQLAlchemy (best-effort)."""
        try:
            from sqlalchemy import text as sa_text

            # We use raw inserts to stay decoupled from the models module
            self.db.execute(
                sa_text(
                    "INSERT OR IGNORE INTO documents "
                    "(id, title, file_path, file_hash, file_type, status) "
                    "VALUES (:id, :title, :fp, :fh, :ft, :st)"
                ),
                {
                    "id": doc_id,
                    "title": meta.get("title", Path(meta.get("file_path", "")).stem),
                    "fp": meta.get("file_path", ""),
                    "fh": file_hash,
                    "ft": meta.get("file_type", ""),
                    "st": "indexed",
                },
            )
            for c in chunks:
                import json

                self.db.execute(
                    sa_text(
                        "INSERT OR IGNORE INTO document_chunks "
                        "(id, document_id, chunk_index, page_number, content, metadata_json) "
                        "VALUES (:id, :doc, :ci, :pn, :ct, :mj)"
                    ),
                    {
                        "id": c["chunk_id"],
                        "doc": doc_id,
                        "ci": c["chunk_index"],
                        "pn": c.get("page_number", 1),
                        "ct": c["content"],
                        "mj": json.dumps(c.get("metadata", {})),
                    },
                )
            self.db.commit()
        except Exception as exc:
            logger.warning("DB save skipped/failed: %s", exc)
