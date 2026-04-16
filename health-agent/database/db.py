"""
Database engine and session management.
"""

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

import config
from database.models import Base

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        connect_args = {}
        if config.DATABASE_URL.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(
            config.DATABASE_URL,
            connect_args=connect_args,
            echo=False,
        )
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(), autocommit=False, autoflush=False
        )
    return _SessionLocal


def init_db() -> None:
    """Create all tables if they don't exist yet."""
    Base.metadata.create_all(bind=get_engine())
    print("Database initialised.")


@contextmanager
def get_session() -> Session:
    """Context manager that provides a transactional database session."""
    SessionLocal = get_session_factory()
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
