import json
import tempfile
from backend.pokemon import Pokedex


def test_pokedex_from_file_tempfile():
    sample = {
        "pokedex_sample": [
            {"poke_id": 1, "name": "Bulbasaur", "types": ["GRASS", "POISON"], "quick_moves": [{"name":"Tackle","type":"NORMAL","power":12}]}
        ]
    }
    with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.json') as f:
        json.dump(sample, f)
        f.flush()
        p = Pokedex.from_file(f.name)
        raw = p.raw()
        assert raw is not None
