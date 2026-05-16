"""SQLAlchemy 2.x engine + session factory.

Supports both PostgreSQL (production) and SQLite (local dev / smoke test).
SQLite is auto-detected from the URL prefix.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

_is_sqlite = settings.database_url.startswith("sqlite")

if _is_sqlite:
    # SQLite engine - no pool_size; allow same-thread sharing for the FastAPI app.
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        future=True,
    )
else:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        future=True,
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
