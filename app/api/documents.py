import logging
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app.agents import rag
from app.config import get_settings
from app.database import get_db
from app.deps import get_current_user
from app.models import Document, User
from app.schemas import DocumentOut

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_TYPES = {"application/pdf", "text/plain", "text/markdown", "text/x-markdown"}
ALLOWED_EXTS = {".pdf", ".txt", ".md"}


@router.post("", response_model=DocumentOut, status_code=201)
async def upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {ext}")

    safe_name = f"{user.id}_{secrets.token_hex(6)}{ext}"
    dest_dir = Path(settings.upload_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / safe_name

    size = 0
    with dest.open("wb") as out:
        while chunk := await file.read(1 << 20):
            size += len(chunk)
            if size > settings.max_upload_mb * 1024 * 1024:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="File too large")
            out.write(chunk)

    namespace = f"user{user.id}_doc{secrets.token_hex(4)}"
    try:
        chunks = rag.index_document(namespace, str(dest), file.content_type or "")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to index document")
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Indexing failed: {exc}") from exc

    doc = Document(
        user_id=user.id,
        filename=file.filename or safe_name,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=size,
        num_chunks=chunks,
        vector_namespace=namespace,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Document).filter(Document.user_id == user.id).order_by(Document.id.desc()).all()


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == user.id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        rag.delete_namespace(doc.vector_namespace)
    except Exception:  # noqa: BLE001
        pass
    db.delete(doc)
    db.commit()
    return Response(status_code=204)
