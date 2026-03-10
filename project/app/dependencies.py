"""
HealthOps Studio — FastAPI Dependencies

WHY THIS FILE EXISTS:
FastAPI's dependency injection system lets us share resources (like DB sessions)
across routes cleanly. Instead of each route manually creating and closing
a session, they declare `db: Session = Depends(get_db)` and FastAPI handles
the lifecycle automatically.

The `yield` in get_db() is key: FastAPI runs the code before yield (open session),
gives it to the route, and after the route completes, runs the code after yield
(close session) — even if the route threw an exception.
"""

from typing import Generator
from sqlalchemy.orm import Session
from app.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency.

    Usage in any route:
        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            return db.query(Item).all()

    The session is automatically closed when the request finishes.
    This prevents connection leaks (your previous code never closed sessions).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
