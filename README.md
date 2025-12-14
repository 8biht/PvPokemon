# PvPokemon
recommendation system for PvP teams in Pokemon GO

Quick start (development)

1. Create and activate a virtual environment (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

3. Start the backend (Flask):

```powershell
# from repo root
python -m flask --app backend.PokeApp --debug run --host 127.0.0.1 --port 5000
```

4. Serve the frontend (static files) in another terminal:

```powershell
python -m http.server 3000 --directory .
# then open http://127.0.0.1:3000/
```

Running tests

Install test requirements and run pytest:

```powershell
pip install -r requirements.txt
pytest -q
```

CI

A GitHub Actions workflow is provided at `.github/workflows/ci.yml` which runs tests on push and PRs to `development` and `main`.

Migrations

For production use Alembic for schema migrations. See `docs/MIGRATIONS.md` for guidance.

Testing

See `docs/TESTING.md` for a testing checklist and local test run instructions. After running tests, add a brief summary to `docs/TEST_RESULTS.md`.

Team members: Cody Benna, Brooklyn Hunt

**Local LAN (phone) testing**

If you want to open the app from a phone on the same Wi‑Fi network, follow these steps.

1. Find your PC's Wi‑Fi IPv4 address (PowerShell):

```powershell
ipconfig
# Look for "IPv4 Address" under your Wi‑Fi adapter (example: 192.168.68.57)
```

2. Start the backend bound to all interfaces (so other devices on the LAN can reach it):

```powershell
$env:FLASK_APP='backend.PokeApp'
$env:FLASK_ENV='development'
python -m flask run --host 0.0.0.0 --port 5000
```

3. Serve the frontend static files and bind to all interfaces:

```powershell
python -m http.server 3000 --bind 0.0.0.0
```

4. Allow the ports through Windows Firewall (run in an elevated PowerShell window if prompted):

```powershell
New-NetFirewallRule -DisplayName "PvPokemon Flask 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "PvPokemon Frontend 3000" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow
```

5. Open the app on your phone (same Wi‑Fi):

- Frontend: http://<PC_IP>:3000 (example: http://192.168.68.57:3000)
- Backend ping/test: http://<PC_IP>:5000/ping (should return {"message":"pong"})

Notes and troubleshooting
- Use the Wi‑Fi adapter IP (not VM/host-only adapters like 192.168.56.x). If you see multiple IPv4 addresses, choose the one tied to your wireless adapter.
- If the phone cannot reach the PC, check router client isolation or try connecting both devices to the same hotspot.
- The frontend now uses the page hostname to build API calls (so the phone points to your PC IP automatically when you open the frontend URL).
- If you prefer not to change firewall/router settings, use a tunneling service like `ngrok` to expose the backend temporarily:

```powershell
ngrok http 5000
```

That will give a public HTTPS URL you can open on your phone. Keep tunnels short-lived and do not expose sensitive data.

Security
- These steps are intended for local development and testing only. Binding to `0.0.0.0` and opening firewall ports exposes the service to your local network — do not use this configuration on untrusted networks.

# PvPokemon Simplified instructions
recommendation system for PvP teams in Pokemon GO

Install Requirements from requirements.txt

Enter directory

In Powershell one run: python -m py_compile "backend\PokeApp.py"

In Powershell one run: python -m flask --app backend.PokeApp --debug run --host 127.0.0.1 --port 5000

In another Powershell, change directories and run: python -m http.server 3000 --directory .

In a browser go to: http://127.0.0.1:3000/#

Team members: Cody Benna, Brooklyn Hunt
