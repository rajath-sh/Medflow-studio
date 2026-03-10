"""
HealthOps Studio — Database Engine & Session Factory

WHY ASYNC IS NOT USED HERE:
For this project, synchronous SQLAlchemy is simpler and sufficient.
FastAPI handles async at the request level; the DB calls happen in a thread pool.
If you needed high-concurrency DB access, you'd switch to asyncpg + async SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import get_settings

settings = get_settings()

# ── Engine ────────────────────────────────────────────────
# The engine manages a pool of database connections.
# pool_pre_ping=True: checks if connections are alive before using them,
# preventing "connection closed" errors after PostgreSQL restarts.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=(settings.APP_ENV == "development"),  # Log SQL in dev only
)

# ── Session Factory ───────────────────────────────────────
# Each request gets its own session (via the get_db dependency).
# autocommit=False: we explicitly control transactions.
# autoflush=False: we explicitly flush when ready.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Declarative Base ──────────────────────────────────────
# All ORM models inherit from this. Using the modern DeclarativeBase
# class (SQLAlchemy 2.0 style) instead of the legacy declarative_base().
class Base(DeclarativeBase):
    pass
