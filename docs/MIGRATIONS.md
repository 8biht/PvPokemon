# Migrations (Alembic) Guidance

This project uses SQLAlchemy for ORM. For production-grade schema changes use Alembic.

Quick start:

1. Install Alembic in your dev environment:

```powershell
pip install alembic
```

2. Initialize Alembic (run once):

```powershell
alembic init alembic
```

3. Configure `alembic.ini` and `alembic/env.py` to point at the `backend.models.sql_models.Base` metadata.
   - See Alembic docs; keep DB URL in environment variables (WRITE_DATABASE_URL).

4. Generate an initial migration after configuring:

```powershell
alembic revision --autogenerate -m "initial models"
alembic upgrade head
```

Notes:
- The repository contains a small runtime helper that will add a nullable `password_hash`
  column to existing SQLite DBs for local development. This is a convenience and should
  not replace proper migrations in production.
