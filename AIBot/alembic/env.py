import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool
from apps.database.database import Base
from alembic import context


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


from apps.database.models import *
target_metadata = Base.metadata



def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    # Преобразуем URL из async в sync (чтобы Alembic мог работать)
    db_url = config.get_main_option("sqlalchemy.url")
    if not db_url:
        raise ValueError("SQLAlchemy URL is not set. Please set the SQL_ALCHEMY_URL environment variable.")
    engine = create_engine(db_url)

    # Создаем синхронный движок для Alembic
    connectable = create_engine(db_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
