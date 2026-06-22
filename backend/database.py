from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.config import settings

# Determine database configurations
DATABASE_URL = settings.DATABASE_URL
is_sqlite = DATABASE_URL.startswith("sqlite")

# Create SQLAlchemy engine
# "connect_args={'check_same_thread': False}" is required ONLY for SQLite
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Declarative Base for models
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency injection helper to yield database sessions.
    Guarantees session closure after HTTP response.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

