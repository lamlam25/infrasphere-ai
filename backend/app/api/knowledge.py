"""
Knowledge Grid Router: Document ingestion, RAG Q&A,
Knowledge Graph, and Contradiction Detection.
"""
from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import get_current_user, require_role
from app.knowledge.answer_generator import RAGAnswerGenerator
from app.knowledge.chunking import TextChunker
from app.knowledge.contradiction import ContradictionDetector
from app.knowledge.graph_builder import KnowledgeGraphBuilder
from app.knowledge.retrieval import RetrievalEngine
from app.models.document import Document, DocumentChunk, DocumentStatus, DocumentVisibility
from app.models.user import User

router = APIRouter(tags=["knowledge"])
chunker = TextChunker()
retrieval_engine = RetrievalEngine()
answer_generator = RAGAnswerGenerator()
graph_builder = KnowledgeGraphBuilder()
contradiction_detector = ContradictionDetector()


class QueryRequest(BaseModel):
    question: str
    incident_id: Optional[str] = None
    language: str = "en"
    top_k: int = 5


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    visibility: str = Form("public"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("analyst", "manager", "admin")),
):
    """Upload PDF, TXT, or Markdown document for automatic ingestion and chunking."""
    filename = file.filename or "uploaded_doc"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".pdf", ".txt", ".md", ".markdown"]:
        raise ValidationError(f"Unsupported format '{ext}'. Allowed: .pdf, .txt, .md")

    content_bytes = await file.read()
    if len(content_bytes) > 10 * 1024 * 1024:
        raise ValidationError("File exceeds 10MB maximum upload limit")

    text_content = ""
    if ext == ".pdf":
        try:
            import fitz
            doc = fitz.open(stream=content_bytes, filetype="pdf")
            for page in doc:
                text_content += page.get_text() + "\n"
        except Exception as e:
            text_content = f"Error extracting PDF text: {e}"
    else:
        text_content = content_bytes.decode("utf-8", errors="replace")

    doc_id = f"DOC-{uuid.uuid4().hex[:6].upper()}"
    doc_title = title or filename

    # Create document record
    doc_record = Document(
        id=doc_id,
        organization_id=current_user.organization_id,
        title=doc_title,
        file_path=filename,
        file_hash=uuid.uuid4().hex,
        file_type=ext[1:],
        version=1,
        status=DocumentStatus.indexed,
        visibility=DocumentVisibility(visibility) if visibility in [v.value for v in DocumentVisibility] else DocumentVisibility.public,
        uploaded_by=current_user.id,
        is_synthetic=True,
    )
    db.add(doc_record)

    # Chunk text
    raw_chunks = chunker.chunk(text_content, {"document_id": doc_id, "title": doc_title})
    for idx, c in enumerate(raw_chunks):
        chunk_rec = DocumentChunk(
            id=f"CHK-{uuid.uuid4().hex[:6].upper()}",
            document_id=doc_id,
            chunk_index=idx,
            page_number=c.get("page_number", 1),
            content=c.get("content", ""),
            metadata_json={"title": doc_title, "chunk_index": idx},
        )
        db.add(chunk_rec)

    await db.commit()

    return {
        "success": True,
        "document_id": doc_id,
        "title": doc_title,
        "chunks_created": len(raw_chunks),
        "status": "indexed",
    }


@router.get("/documents")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(select(Document).order_by(Document.created_at.desc()))
    docs = res.scalars().all()
    return [
        {
            "id": d.id,
            "title": d.title,
            "file_type": d.file_type,
            "version": d.version,
            "status": d.status.value if hasattr(d.status, "value") else str(d.status),
            "visibility": d.visibility.value if hasattr(d.visibility, "value") else str(d.visibility),
            "is_synthetic": d.is_synthetic,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]


@router.get("/documents/{id}")
async def get_document_details(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(select(Document).where(Document.id == id))
    doc = res.scalar_one_or_none()
    if not doc:
        raise NotFoundError(f"Document '{id}' not found")

    res_chunks = await db.execute(select(DocumentChunk).where(DocumentChunk.document_id == id))
    chunks = res_chunks.scalars().all()

    return {
        "id": doc.id,
        "title": doc.title,
        "file_type": doc.file_type,
        "version": doc.version,
        "status": doc.status.value if hasattr(doc.status, "value") else str(doc.status),
        "chunk_count": len(chunks),
        "chunks": [
            {
                "id": c.id,
                "chunk_index": c.chunk_index,
                "page_number": c.page_number,
                "content": c.content,
            }
            for c in chunks
        ],
    }


@router.delete("/documents/{id}")
async def delete_document(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("manager", "admin")),
):
    res = await db.execute(select(Document).where(Document.id == id))
    doc = res.scalar_one_or_none()
    if not doc:
        raise NotFoundError(f"Document '{id}' not found")
    await db.delete(doc)
    await db.commit()
    return {"success": True, "message": f"Document '{id}' deleted"}


@router.post("/knowledge/query")
async def query_knowledge_grid(
    req: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """RAG Question Answering: retrieves evidence chunks and returns citations."""
    res_chunks = await db.execute(select(DocumentChunk).limit(10))
    all_chunks = res_chunks.scalars().all()

    # Score chunks against question
    scored_chunks = []
    q_words = set(req.question.lower().split())
    for c in all_chunks:
        overlap = len(set(c.content.lower().split()) & q_words)
        score = min(1.0, 0.4 + (overlap * 0.15))
        scored_chunks.append({
            "chunk_id": c.id,
            "document_id": c.document_id,
            "page_number": c.page_number,
            "content": c.content,
            "score": score,
            "metadata": c.metadata_json or {},
        })

    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    top_chunks = scored_chunks[:req.top_k]

    answer_res = answer_generator.generate(
        question=req.question,
        chunks=top_chunks,
        language=req.language,
    )

    return answer_res


@router.get("/knowledge/graph")
async def get_knowledge_graph(
    center_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return nodes and edges formatted for React Flow knowledge graph visualization."""
    return graph_builder.get_graph_data(center_id)


@router.get("/knowledge/conflicts")
async def get_document_conflicts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Detect and return contradictory statements across operational documents."""
    res_chunks = await db.execute(select(DocumentChunk))
    chunks = [
        {
            "chunk_id": c.id,
            "document_id": c.document_id,
            "content": c.content,
            "page_number": c.page_number,
            "metadata": c.metadata_json or {},
        }
        for c in res_chunks.scalars().all()
    ]
    conflicts = contradiction_detector.detect(chunks)
    return {
        "total_conflicts_found": len(conflicts),
        "conflicts": conflicts,
    }
