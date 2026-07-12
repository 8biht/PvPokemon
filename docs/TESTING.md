# Testing Checklist

This document describes the manual and automated testing steps for PvPokemon.

Automated tests (pytest)
- [ ] Unit tests: repository, DTOs, service logic
- [ ] Integration tests: auth endpoints, box endpoints
- [ ] Run: `pytest -q`

Functional tests
- [ ] Signup/login/refresh/logout flows
- [ ] Box CRUD: add/update/remove/get
- [ ] Recommender endpoint

Non-functional checks
- [ ] Startup time (dev): < 3s ideally on local machine
- [ ] Assets listing returns PNGs

How to run locally

1. Create a virtualenv and install requirements:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

2. Run tests:

```powershell
pytest -q
```

Test results summary

Run tests locally and paste summarized output here. Create `docs/TEST_RESULTS.md` with pass/fail counts after running.
