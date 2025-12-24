"""Simple retrieval helper backed by FAISS and SentenceTransformers embeddings."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence

import faiss  # type: ignore
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DocumentChunk

# Use a lightweight but effective model for embeddings
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBED_DIM = 384  # Dimension for all-MiniLM-L6-v2 model


@lru_cache(maxsize=1)
def _get_embedding_model() -> SentenceTransformer:
    """Load the SentenceTransformer model once and cache it."""
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_text(text: str) -> np.ndarray:
    """Create a semantic embedding using SentenceTransformers."""
    model = _get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
    return embedding.astype("float32")


@dataclass
class RetrievedContext:
    content: str
    source: str
    score: float


class Retriever:
    """Tiny wrapper around a FAISS index for context retrieval."""

    def __init__(self, chunks: Sequence[DocumentChunk]):
        self.chunks = list(chunks)
        if not self.chunks:
            self.index = None
            return

        self.index = faiss.IndexFlatL2(EMBED_DIM)
        embeddings = np.stack([np.array(chunk.embedding, dtype="float32") for chunk in self.chunks])
        self.index.add(embeddings)

    def search(self, query: str, k: int = 3) -> list[RetrievedContext]:
        if not self.index or not self.chunks:
            return []

        query_vector = np.expand_dims(embed_text(query), axis=0)
        distances, indices = self.index.search(query_vector, min(k, len(self.chunks)))
        results: list[RetrievedContext] = []
        for score, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            chunk = self.chunks[idx]
            results.append(
                RetrievedContext(content=chunk.content, source=chunk.source, score=float(score))
            )
        return results


def ensure_embeddings(db: Session) -> list[DocumentChunk]:
    """Compute embeddings for stored chunks when they are missing."""
    chunks = db.execute(select(DocumentChunk)).scalars().all()
    updated = False
    for chunk in chunks:
        if not chunk.embedding:
            vector = embed_text(chunk.content)
            chunk.embedding = vector.tolist()
            db.add(chunk)
            updated = True
    if updated:
        db.commit()
    return chunks


@lru_cache(maxsize=1)
def _empty_retriever() -> Retriever:
    return Retriever([])


def build_retriever(db: Session) -> Retriever:
    """Load chunks from the database and construct a FAISS-backed retriever."""
    chunks = ensure_embeddings(db)
    if not chunks:
        return _empty_retriever()
    return Retriever(chunks)
