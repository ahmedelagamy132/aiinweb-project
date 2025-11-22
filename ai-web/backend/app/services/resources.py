"""Service helpers for the resource catalog feature."""

from __future__ import annotations

from typing import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Resource


def list_resources(db: Session) -> Sequence[Resource]:
    """Return resources ordered by recency."""

    return db.execute(select(Resource).order_by(Resource.created_at.desc())).scalars().all()


def create_resource(db: Session, *, title: str, description: str, url: str, difficulty: str) -> Resource:
    """Persist a new resource entry."""

    record = Resource(title=title, description=description, url=url, difficulty=difficulty)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def seed_resources(db: Session, resources: Iterable[dict[str, str]]) -> None:
    """Populate initial demo resources if the table is empty."""

    if db.execute(select(Resource).limit(1)).scalar_one_or_none():
        return

    for entry in resources:
        db.add(Resource(**entry))
    db.commit()

