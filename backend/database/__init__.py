"""
Database Infrastructure Layer (Migrations, Seeds, and Base Configs)
==================================================================

This module handles database initialization scripts, data seeds, and 
alembic migration helper structures.

It works in tandem with backend/models to manage connection pools, 
schema modifications, and initial mockup resource data (e.g. mock hospitals, 
available ambulances, and patient profiles).
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.config import settings

# Retrieve database connection string
DATABASE_URL = settings.DATABASE_URL
is_sqlite = DATABASE_URL.startswith("sqlite")

# Configure database engine
# connect_args={'check_same_thread': False} is required only for SQLite
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG
)

# Session factory for database transactions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Declarative base model class
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency injection generator providing isolated database sessions.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
