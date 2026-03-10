from .database import engine
from .db_models import Base


def init_db():
    Base.metadata.create_all(bind=engine)
