import os
from typing import Any

from .config import get_config


def get_repository(data_dir: str) -> Any:
    cfg = get_config()
    impl = cfg.REPOSITORY_IMPL.lower()
    if impl in ('sql', 'sqlalchemy', 'db'):
        # Lazy import to avoid importing SQLAlchemy when not needed
        from .repositories.sqlalchemy_repo import SQLAlchemyBoxesRepository
        db_url = cfg.DATABASE_URL
        return SQLAlchemyBoxesRepository(db_url)
    else:
        # JSON repository has been retired. If you explicitly request it, raise an error.
        raise NotImplementedError("JSON repository implementation has been retired. Use 'sqlalchemy' as REPOSITORY_IMPL or remove the explicit setting.")
