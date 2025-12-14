import os
import importlib
from pathlib import Path

import pytest


@pytest.fixture(scope='session')
def test_env(tmp_path_factory):
    """Prepare environment variables for tests and import the app module.

    Uses a file-backed SQLite DB in a temporary directory so SQLAlchemy's
    engines can share the same file across read/write engines.
    """
    tmpdir = tmp_path_factory.mktemp('testdata')
    db_path = tmpdir / 'test.db'
    url = f"sqlite:///{db_path.as_posix()}"
    # set env vars before importing the app so config picks them up
    os.environ['WRITE_DATABASE_URL'] = url
    os.environ['READ_DATABASE_URL'] = url
    os.environ['BACKEND_REPO'] = 'sqlalchemy'
    # ensure a predictable JWT secret for tests
    os.environ['JWT_SECRET'] = 'test-secret'

    # import the app module after env vars are set
    import backend.PokeApp as appmod
    importlib.reload(appmod)

    yield appmod
