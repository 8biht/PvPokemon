import os
from typing import Optional


class Config:
    # Choose repository implementation: 'json' or 'sqlalchemy'
    # Default to 'sqlalchemy' so the app uses the SQLite repository by default.
    REPOSITORY_IMPL = os.getenv('BACKEND_REPO', 'sqlalchemy')
    # Database URLs. If READ/WRITE separation is desired, set both:
    # - WRITE_DATABASE_URL: used for writes (primary)
    # - READ_DATABASE_URL: used for reads (replica)
    # If only DATABASE_URL or WRITE_DATABASE_URL is provided, the repo will
    # fall back to a single-connection mode.
    DATABASE_URL = os.getenv('DATABASE_URL')
    WRITE_DATABASE_URL = os.getenv('WRITE_DATABASE_URL') or os.getenv('DATABASE_URL')
    READ_DATABASE_URL = os.getenv('READ_DATABASE_URL') or os.getenv('DATABASE_URL')
    # Assets dir override
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    ASSETS_DIR = os.getenv('ASSETS_DIR') or os.path.join(BASE_DIR, 'PokeMiners pogo_assets master Images-Pokemon - 256x256')


def get_config() -> Config:
    return Config()
