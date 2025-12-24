#!/usr/bin/env python3
"""Script to ingest logistics documentation into the database for RAG retrieval.

This script reads text files from the data/ directory, splits them into chunks,
generates embeddings using SentenceTransformers, and stores them in the database.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Add parent directory to path to import app modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import get_settings
from app.database import Base
from app.models import DocumentChunk
from app.services.rag import embed_text


def chunk_document(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split document into overlapping chunks by sentences."""
    # Split into sentences (simple approach)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence)
        
        # If adding this sentence exceeds chunk size and we have content, save chunk
        if current_length + sentence_length > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            # Keep last few sentences for overlap
            overlap_sentences = []
            overlap_length = 0
            for s in reversed(current_chunk):
                if overlap_length + len(s) <= overlap:
                    overlap_sentences.insert(0, s)
                    overlap_length += len(s)
                else:
                    break
            current_chunk = overlap_sentences
            current_length = overlap_length
        
        current_chunk.append(sentence)
        current_length += sentence_length
    
    # Add final chunk
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks


def ingest_file(db: Session, file_path: Path, slug: str) -> int:
    """Read a file, chunk it, generate embeddings, and store in database."""
    print(f"Processing {file_path.name}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove existing chunks for this slug to avoid duplicates
    db.query(DocumentChunk).filter(DocumentChunk.slug == slug).delete()
    
    chunks = chunk_document(content)
    print(f"  Split into {len(chunks)} chunks")
    
    for i, chunk_text in enumerate(chunks):
        # Generate embedding
        embedding = embed_text(chunk_text)
        
        # Create database entry
        chunk = DocumentChunk(
            slug=f"{slug}_chunk_{i}",
            source=file_path.name,
            content=chunk_text,
            embedding=embedding.tolist()
        )
        db.add(chunk)
    
    db.commit()
    print(f"  Ingested {len(chunks)} chunks from {file_path.name}")
    return len(chunks)


def main():
    """Main ingestion workflow."""
    print("=== Document Ingestion Script ===\n")
    
    # Get database URL from settings
    settings = get_settings()
    engine = create_engine(settings.database_url)
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    db = Session(engine)
    
    # Find all .txt files in data directory
    data_dir = Path(__file__).parent / 'data'
    if not data_dir.exists():
        print(f"Error: Data directory not found at {data_dir}")
        return
    
    txt_files = list(data_dir.glob('*.txt'))
    if not txt_files:
        print(f"No .txt files found in {data_dir}")
        return
    
    print(f"Found {len(txt_files)} document(s) to ingest:\n")
    
    total_chunks = 0
    for file_path in txt_files:
        # Use filename (without extension) as slug
        slug = file_path.stem
        chunks_added = ingest_file(db, file_path, slug)
        total_chunks += chunks_added
    
    print(f"\n✓ Successfully ingested {total_chunks} total chunks from {len(txt_files)} documents")
    print(f"✓ Embeddings generated using SentenceTransformers (all-MiniLM-L6-v2)")
    print(f"✓ Documents are now available for RAG retrieval in the agent system")
    
    db.close()


if __name__ == '__main__':
    main()
