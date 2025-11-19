# PvPokemon
recommendation system for PvP teams in Pokemon GO

As of right now to run the app

Install Requirements from requirements.txt

Enter directory

In Powershell one run: python -m py_compile "backend\PokeApp.py"

In Powershell one run: python -m flask --app backend.PokeApp --debug run --host 127.0.0.1 --port 5000

In another Powershell, change directories and run: python -m http.server 3000 --directory .

In a browser go to: http://127.0.0.1:3000/#

Team members: Cody Benna, Brooklyn Hunt
