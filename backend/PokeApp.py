from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

def create_app(config=None):
    """Return the Flask app instance. For tests or WSGI servers call this.
    This project currently constructs the app at module import; this wrapper
    makes it easier to obtain the app object programmatically.
    """
    return app

# Base and data directories
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# Path to the bundled sprite assets in the repository
ASSETS_DIR = os.path.join(BASE_DIR, 'PokeMiners pogo_assets master Images-Pokemon - 256x256')

os.makedirs(DATA_DIR, exist_ok=True)

from .config import get_config
from .repo_factory import get_repository
from .services import BoxService
from . import command_handlers
from . import projections
from .pokemon import Pokedex

# Initialize config and repository
cfg = get_config()
repo = get_repository(DATA_DIR)

# Try to load a pokedex JSON (user-provided) from the data folder
POKEDEX_PATH = os.path.join(DATA_DIR, 'pokedex.json')
pokedex = Pokedex.from_file(POKEDEX_PATH)

# Create the service and pass the loaded pokedex so server-side validation
# can consult known quick/charge moves when adding Pokemon to a box.
service = BoxService(repo, cfg.ASSETS_DIR, pokedex=pokedex)
# register simple in-process projections (read-model updaters) so events update
# a read-side snapshot under backend/data/read_models. This demonstrates EDA.
try:
    projections.register_default_projections()
except Exception:
    # non-fatal if projections fail to register
    pass


@app.route('/')
def index():
    return jsonify(message="Welcome to PokeApp Backend")


@app.route('/ping')
def ping():
    return jsonify(message="pong")


@app.route('/api/v1/sprites')
def list_sprites():
    """Return a list of available sprite filenames."""
    if not os.path.isdir(ASSETS_DIR):
        return jsonify(error="Assets folder not found"), 500
    files = [f for f in os.listdir(ASSETS_DIR) if f.lower().endswith('.png')]
    files.sort()
    return jsonify(sprites=files)


@app.route('/api/v1/pokedex/raw')
def pokedex_raw():
    """Return the raw JSON loaded from backend/data/pokedex.json (if any)."""
    raw = pokedex.raw()
    if raw is None:
        return jsonify(error='No pokedex file loaded'), 404
    return jsonify(raw)


@app.route('/api/v1/pokedex')
def pokedex_list():
    """Return a simplified list of pokedex entries if available.

    If the loaded pokedex produced Pokemon objects (indexed by dexNr), return those.
    Otherwise, if the raw JSON contains a `pokedex_sample` array (placeholder), return it.
    """
    all_p = pokedex.all()
    if all_p:
        return jsonify(pokedex=[p.to_dict() for p in all_p])

    raw = pokedex.raw()
    if isinstance(raw, dict) and 'pokedex_sample' in raw:
        return jsonify(pokedex=raw['pokedex_sample'])

    # fallback: return a helpful message and the raw content
    if raw is not None:
        return jsonify(message='Pokedex loaded but no indexed entries available; use /api/v1/pokedex/raw to see raw file', raw_summary=bool(raw)), 200
    return jsonify(error='No pokedex file found'), 404


@app.route('/api/v1/pokedex/<int:dex_nr>')
def pokedex_get(dex_nr: int):
    p = pokedex.get(dex_nr)
    if p is None:
        return jsonify(error='Pokemon not found for dexNr {}'.format(dex_nr)), 404
    return jsonify(pokedex=p.to_dict())


@app.route('/assets/<path:filename>')
def serve_asset(filename):
    """Serve a sprite from the bundled assets folder."""
    if not os.path.isdir(ASSETS_DIR):
        abort(404)
    safe_path = os.path.normpath(os.path.join(ASSETS_DIR, filename))
    if not safe_path.startswith(os.path.abspath(ASSETS_DIR)):
        abort(403)
    if not os.path.exists(safe_path):
        abort(404)
    return send_from_directory(ASSETS_DIR, filename)


@app.route('/api/v1/box/<string:user_id>', methods=['GET'])
def get_box(user_id):
    try:
        box = service.get_box(user_id)
        return jsonify(box=box)
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/api/v1/box/<string:user_id>', methods=['POST'])
def add_to_box(user_id):
    payload = request.get_json(force=True, silent=True)
    if not payload:
        return jsonify(error='Invalid JSON body'), 400
    name = payload.get('name')
    sprite = payload.get('sprite')
    cp = payload.get('cp')
    quick_move = payload.get('quick_move')
    # accept either 'charge_move' (string) or 'charge_moves' (array)
    charge_moves = payload.get('charge_moves') if 'charge_moves' in payload else (
        [payload.get('charge_move')] if payload.get('charge_move') is not None else None
    )

    if not sprite:
        return jsonify(error='Missing sprite'), 400

    try:
        box = command_handlers.handle_add_to_box(service, user_id, name, sprite, cp, quick_move=quick_move, charge_moves=charge_moves)
        return jsonify(box=box)
    except FileNotFoundError as fe:
        return jsonify(error=str(fe), sprite=sprite), 400
    except ValueError as ve:
        return jsonify(error=str(ve)), 400
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/api/v1/box/<string:user_id>/<int:slot>', methods=['DELETE'])
def remove_from_box(user_id, slot):
    try:
        removed, box = command_handlers.handle_remove_from_box(service, user_id, slot)
        return jsonify(removed=removed, box=box)
    except IndexError:
        return jsonify(error='Invalid slot index'), 400
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/api/v1/box/<string:user_id>/<int:slot>', methods=['PUT'])
def update_box_entry(user_id, slot):
    payload = request.get_json(force=True, silent=True)
    if not payload:
        return jsonify(error='Invalid JSON body'), 400
    name = payload.get('name')
    sprite = payload.get('sprite')
    cp = payload.get('cp')
    quick_move = payload.get('quick_move')
    charge_moves = payload.get('charge_moves') if 'charge_moves' in payload else (
        [payload.get('charge_move')] if payload.get('charge_move') is not None else None
    )

    if not sprite:
        return jsonify(error='Missing sprite'), 400

    try:
        box = command_handlers.handle_update_box_entry(service, user_id, slot, name, sprite, cp, quick_move=quick_move, charge_moves=charge_moves)
        return jsonify(box=box)
    except FileNotFoundError as fe:
        return jsonify(error=str(fe), sprite=sprite), 400
    except ValueError as ve:
        return jsonify(error=str(ve)), 400
    except IndexError:
        return jsonify(error='Invalid slot index'), 400
    except Exception as e:
        return jsonify(error=str(e)), 500


if __name__ == '__main__':
    app.run(debug=True)

