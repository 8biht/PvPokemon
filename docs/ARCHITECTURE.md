# PvPokemon - Architecture Overview

Location: `docs/ARCHITECTURE.md`

Purpose
- Provide a compact, practical overview of the current code structure and recommended next steps for production readiness.

Layered design (current)
- Presentation (frontend): `index.html` — static UI that calls backend APIs.
- API / Controller: `backend/PokeApp.py` — Flask routes that accept requests and return JSON.
- Service layer: `backend/services.py` — business rules and validation (BoxService).
- Repository / Persistence: `backend/repository.py` — file-based JSON storage (BoxesRepository). Swap for a DB later.
- Domain / DTOs: `backend/dto.py` — `BoxEntry` dataclass used to pass data between layers.

Why this layout?
- Separates responsibilities: handlers stay thin, business rules are testable in services, and persistence details are isolated in repository classes.

Production recommendations
- Replace file-based JSON with a transactional DB (SQLite for local / Postgres for production).
- Add migrations and a small repository interface/adapter to keep switching stores simple.
- Add authentication (JWT or session-based) and rate-limiting for public endpoints.
- Add logging, structured errors, and input validation (e.g., Marshmallow or Pydantic) for stricter schemas.

Operational notes
- The current assets folder is referenced from `PokeApp.py` as:
  `PokeMiners pogo_assets master Images-Pokemon - 256x256` at repo root. Consider moving assets under `backend/assets` and normalizing filenames.
- The project currently runs with Flask in development mode; use a WSGI server (Gunicorn/uvicorn) behind a reverse proxy for production.

Next steps to complete sprint
1. Formalize DB schema and add a migration script that imports `backend/data/boxes.json` into the DB.
2. Add an OpenAPI spec and small client SDK generator if needed.
3. Refactor further to separate Flask app factory and configuration (e.g., `create_app(config_name)`), which helps testing.
4. Add a small `manage_db.py` utility to initialize the database and import existing JSON box data (already added at `backend/manage_db.py`).
5. Add a minimal OpenAPI spec at `docs/openapi.yaml` (already added) to document routes and payloads for QA and client dev.
6. Add a CI pipeline (GitHub Actions) that runs tests on push/PR (skeleton added at `.github/workflows/ci.yml`).

Notes on app factory:
- A lightweight `create_app()` wrapper was added to `backend/PokeApp.py` so WSGI servers and tests can obtain the Flask app programmatically. For full testability consider refactoring route creation into a factory that accepts injected dependencies (repository, config).

Migration guidance:
- The project currently includes `backend/manage_db.py` which can create the DB and import the existing `backend/data/boxes.json` into the SQLAlchemy store.
- For production-grade migration support, add Alembic and a versioned migration workflow.
