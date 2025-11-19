import os
from typing import Optional


class Config:
    # Choose repository implementation: 'json' or 'sqlalchemy'
    # Default to 'sqlalchemy' so the app uses the SQLite repository by default.
    REPOSITORY_IMPL = os.getenv('BACKEND_REPO', 'sqlalchemy')
    # SQLite DB URL (used when REPOSITORY_IMPL == 'sqlalchemy')
    DATABASE_URL = os.getenv('DATABASE_URL')
    # Assets dir override
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    ASSETS_DIR = os.getenv('ASSETS_DIR') or os.path.join(BASE_DIR, 'PokeMiners pogo_assets master Images-Pokemon - 256x256')


def get_config() -> Config:
    return Config()
