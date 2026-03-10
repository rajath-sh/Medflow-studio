"""
HealthOps Studio — Alembic Migration Environment

This file tells Alembic how to connect to the database and
where to find the models for auto-generating migrations.

Key change from default: we get the database URL from our
config module instead of alembic.ini, so it reads from .env.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Import our database setup — this makes Alembic aware of all our models
from app.database import Base, engine
from app.db_models import *  # noqa: F401, F403 — ensures all models are registered
from app.config import get_settings

# Alembic Config object
config = context.config

# Override the sqlalchemy URL with our env-based config
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Set up Python logging from the config file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Tell Alembic about our model metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations without an active database connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations with a live database connection."""
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
