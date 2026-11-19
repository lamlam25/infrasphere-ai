"""Text chunking for the Knowledge Grid."""
from __future__ import annotations

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Rough chars-per-token approximation (English text)
_CHARS_PER_TOKEN = 4


class TextChunker:
    """
    Splits text at sentence/paragraph boundaries.

    Each returned chunk is a dict:
        {
            content: str,
            chunk_index: int,
            char_start: int,
            char_end: int,
            metadata: dict,
        }

    Default target: 500-800 tokens (~2000-3200 chars) with ~100 token overlap.
    chunk_size=600 tokens, overlap=100 tokens by default.
    """

    def __init__(self, chunk_size: int = 600, overlap: int = 100):
        self.chunk_size = chunk_size  # tokens
        self.overlap = overlap  # tokens
        self._chunk_chars = chunk_size * _CHARS_PER_TOKEN
        self._overlap_chars = overlap * _CHARS_PER_TOKEN

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split *text* into overlapping chunks, respecting paragraph and
        sentence boundaries as much as possible.
        """
        if not text or not text.strip():
            return []

        paragraphs = self._split_paragraphs(text)
        raw_chunks = self._merge_paragraphs(paragraphs)
        chunks: List[Dict[str, Any]] = []

        for idx, (content, char_start, char_end) in enumerate(raw_chunks):
            chunks.append(
                {
                    "content": content,
                    "chunk_index": idx,
                    "char_start": char_start,
                    "char_end": char_end,
                    "metadata": {**metadata},
                }
            )

        return chunks

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _split_paragraphs(self, text: str) -> List[tuple[str, int, int]]:
        """Return (paragraph_text, start, end) triples."""
        paragraphs: List[tuple[str, int, int]] = []
        for m in re.finditer(r"\S[\s\S]*?(?=\n{2,}|\Z)", text):
            paragraphs.append((m.group(), m.start(), m.end()))
        if not paragraphs:
            paragraphs = [(text, 0, len(text))]
        return paragraphs

    def _split_sentences(self, text: str, offset: int = 0) -> List[tuple[str, int, int]]:
        """Split a paragraph into sentences."""
        sentence_re = re.compile(r"(?<=[.!?])\s+(?=[A-Z\u0980-\u09FF])")
        sentences: List[tuple[str, int, int]] = []
        prev = 0
        for m in sentence_re.finditer(text):
            s = text[prev : m.start() + 1].strip()
            if s:
                s_start = offset + text.find(s, prev)
                sentences.append((s, s_start, s_start + len(s)))
            prev = m.end()
        tail = text[prev:].strip()
        if tail:
            t_start = offset + text.find(tail, prev)
            sentences.append((tail, t_start, t_start + len(tail)))
        if not sentences:
            sentences = [(text.strip(), offset, offset + len(text.strip()))]
        return sentences

    def _merge_paragraphs(
        self, paragraphs: List[tuple[str, int, int]]
    ) -> List[tuple[str, int, int]]:
        """
        Greedily merge paragraphs into chunks of ≤ chunk_chars.
        When a single paragraph exceeds chunk_chars, split it at sentence
        boundaries with overlap.
        """
        chunks: List[tuple[str, int, int]] = []
        buffer_parts: List[tuple[str, int, int]] = []
        buffer_len = 0

        def flush(buf: List[tuple[str, int, int]]) -> None:
            if not buf:
                return
            content = "\n\n".join(p for p, _, _ in buf)
            start = buf[0][1]
            end = buf[-1][2]
            chunks.append((content, start, end))

        for para, p_start, p_end in paragraphs:
            if len(para) > self._chunk_chars:
                # flush buffer first
                flush(buffer_parts)
                buffer_parts, buffer_len = [], 0
                # split this large paragraph at sentence boundaries
                sentences = self._split_sentences(para, offset=p_start)
                self._chunk_sentences(sentences, chunks)
            else:
                if buffer_len + len(para) > self._chunk_chars and buffer_parts:
                    flush(buffer_parts)
                    # keep overlap: last few sentences of current buffer
                    overlap_buf = self._overlap_tail(buffer_parts)
                    buffer_parts = overlap_buf
                    buffer_len = sum(len(p) for p, _, _ in buffer_parts)
                buffer_parts.append((para, p_start, p_end))
                buffer_len += len(para)

        flush(buffer_parts)
        return chunks

    def _chunk_sentences(
        self,
        sentences: List[tuple[str, int, int]],
        out: List[tuple[str, int, int]],
    ) -> None:
        """Pack sentences into chunks with overlap."""
        i = 0
        while i < len(sentences):
            buf: List[tuple[str, int, int]] = []
            buf_len = 0
            j = i
            while j < len(sentences) and buf_len + len(sentences[j][0]) <= self._chunk_chars:
                buf.append(sentences[j])
                buf_len += len(sentences[j][0])
                j += 1
            if not buf:
                buf = [sentences[j]]
                j += 1
            content = " ".join(s for s, _, _ in buf)
            out.append((content, buf[0][1], buf[-1][2]))
            # advance by (chunk - overlap)
            step = max(1, len(buf) - max(1, int(self.overlap / (self.chunk_size / max(1, len(buf))))))
            i += step

    def _overlap_tail(self, buf: List[tuple[str, int, int]]) -> List[tuple[str, int, int]]:
        """Return the last N chars worth of items for overlap."""
        total = 0
        result: List[tuple[str, int, int]] = []
        for item in reversed(buf):
            total += len(item[0])
            result.insert(0, item)
            if total >= self._overlap_chars:
                break
        return result
