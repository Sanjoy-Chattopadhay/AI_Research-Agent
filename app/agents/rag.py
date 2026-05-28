"""Retrieval-Augmented Generation with FAISS + local Hugging Face embeddings.

Each user gets a namespaced FAISS index on disk so uploaded PDFs / text files
can be queried alongside web tools. Embeddings use the (free) sentence-transformers
all-MiniLM-L6-v2 model — small, fast, and runs on CPU.
"""
from __future__ import annotations

import logging
import os
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_embedder = None
_faiss = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model %s ...", settings.embedding_model)
        _embedder = SentenceTransformer(settings.embedding_model)
    return _embedder


def _get_faiss():
    global _faiss
    if _faiss is None:
        import faiss  # type: ignore

        _faiss = faiss
    return _faiss


@dataclass
class Chunk:
    text: str
    source: str
    chunk_index: int


def _namespace_dir(namespace: str) -> Path:
    p = Path(settings.vector_store_dir) / namespace
    p.mkdir(parents=True, exist_ok=True)
    return p


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    text = text.replace("\r\n", "\n")
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = end - overlap
    return chunks


def extract_text(file_path: str, content_type: str) -> str:
    """Extract plain text from PDF / TXT / MD files."""
    p = Path(file_path)
    suffix = p.suffix.lower()
    if suffix == ".pdf" or content_type == "application/pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(p))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    return p.read_text(encoding="utf-8", errors="ignore")


def index_document(namespace: str, file_path: str, content_type: str) -> int:
    """Embed and store a document under the given namespace. Returns chunk count."""
    text = extract_text(file_path, content_type)
    if not text.strip():
        return 0

    chunks = _chunk_text(text)
    if not chunks:
        return 0

    embedder = _get_embedder()
    faiss = _get_faiss()
    vectors = embedder.encode(chunks, normalize_embeddings=True, show_progress_bar=False)
    vectors = np.asarray(vectors, dtype="float32")

    ns_dir = _namespace_dir(namespace)
    index_path = ns_dir / "index.faiss"
    meta_path = ns_dir / "meta.pkl"

    if index_path.exists() and meta_path.exists():
        index = faiss.read_index(str(index_path))
        with open(meta_path, "rb") as f:
            metas: list[Chunk] = pickle.load(f)
    else:
        index = faiss.IndexFlatIP(vectors.shape[1])
        metas = []

    index.add(vectors)
    source = Path(file_path).name
    for i, c in enumerate(chunks):
        metas.append(Chunk(text=c, source=source, chunk_index=i))

    faiss.write_index(index, str(index_path))
    with open(meta_path, "wb") as f:
        pickle.dump(metas, f)

    return len(chunks)


def search(namespace: str, query: str, k: int = 4) -> list[Chunk]:
    ns_dir = _namespace_dir(namespace)
    index_path = ns_dir / "index.faiss"
    meta_path = ns_dir / "meta.pkl"
    if not index_path.exists() or not meta_path.exists():
        return []

    faiss = _get_faiss()
    embedder = _get_embedder()
    index = faiss.read_index(str(index_path))
    with open(meta_path, "rb") as f:
        metas: list[Chunk] = pickle.load(f)

    qv = embedder.encode([query], normalize_embeddings=True, show_progress_bar=False)
    qv = np.asarray(qv, dtype="float32")
    distances, indices = index.search(qv, min(k, len(metas)))
    return [metas[i] for i in indices[0] if 0 <= i < len(metas)]


def build_context(namespace: str, query: str, k: int = 4) -> str:
    chunks = search(namespace, query, k=k)
    if not chunks:
        return ""
    formatted = []
    for i, c in enumerate(chunks, 1):
        formatted.append(f"[{i}] ({c.source}#chunk{c.chunk_index})\n{c.text}")
    return "\n\n".join(formatted)


def delete_namespace(namespace: str) -> None:
    ns_dir = _namespace_dir(namespace)
    for f in ns_dir.iterdir():
        try:
            f.unlink()
        except OSError:
            pass
    try:
        os.rmdir(ns_dir)
    except OSError:
        pass
