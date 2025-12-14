# Test Results

Latest test run (local developer run)

- Date: 2025-12-14
- Environment: Windows, Python 3.13 (local dev)
- Command used: `python -m pytest -q`

Summary:

- Total tests run: 4
- Passed: 4
- Failed: 0
- Warnings: 2 (see notes)
- Total time: ~1.4s

Full pytest exit summary (trimmed):

```
....                                                                                                        [100%]

4 passed, 2 warnings in 1.42s
```

Tests included

- `tests/test_auth.py` — signup/login/refresh/logout flow (integration using Flask test client)
- `tests/test_repo.py` — repository CRUD and refresh token behavior
- `tests/test_boxservice.py` — box service add/update/remove (including in-memory sqlite case)

Notes

- Two DeprecationWarnings were observed during the run originating from `backend/PokeApp.py` (use of `datetime.utcnow()`): consider migrating to timezone-aware datetimes.
- The repository includes a small runtime SQLite helper to add nullable `password_hash` for local DBs; for production use scaffold Alembic migrations (see `docs/MIGRATIONS.md`).
