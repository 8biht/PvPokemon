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
from .di import build_container
import uuid
import datetime
import jwt
import importlib

# Defensive check: if the imported `jwt` module doesn't provide `encode`,
# give a clear runtime hint so users can install the correct package
# (PyJWT) or remove a conflicting `jwt` module from their PYTHONPATH.
_JWT_MODULE_PATH = getattr(jwt, '__file__', '<built-in or unknown>')
_JWT_HAS_ENCODE = hasattr(jwt, 'encode')
if not _JWT_HAS_ENCODE:
    # attempt to show what package is available
    try:
        pkg = importlib.import_module('jwt')
        _JWT_MODULE_PATH = getattr(pkg, '__file__', _JWT_MODULE_PATH)
    except Exception:
        pass
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize wiring via DI container (composition root)
container = build_container(DATA_DIR)
cfg = container.cfg
repo = container.repo
pokedex = container.pokedex
service = container.service

# Ensure repository runtime migration helper runs (SQLite dev DBs) to add
# `password_hash` column or other small schema fixes if the DB predates models.
try:
    _helper = getattr(repo, '_ensure_users_password_column', None)
    if callable(_helper):
        try:
            _helper()
        except Exception:
            # best-effort, non-fatal
            pass
except Exception:
    pass
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


@app.route('/api/v1/users', methods=['POST'])
def create_user():
    """Create a new user with the provided id (username).

    Body: { "id": "username" }
    The server will create a `User` record if it does not already exist.
    This endpoint is idempotent and returns `{ created: bool, id: <id> }`.
    """
    payload = request.get_json(force=True, silent=True) or {}
    uid = payload.get('id') or payload.get('username')
    if not uid or not isinstance(uid, str) or not uid.strip():
        return jsonify(error='Missing or invalid id/username'), 400
    uid = uid.strip()
    try:
        # If repository supports ensure_user, use it. Otherwise try service.
        created = False
        try:
            created = repo.ensure_user(uid)
        except Exception:
            try:
                created = service.create_user(uid)
            except Exception:
                # fallback: no-op but return success (idempotent)
                created = False
        return jsonify(created=bool(created), id=uid)
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/api/v1/recommend', methods=['POST'])
def recommend_team():
    """Return a recommended team of 3 pokemons.

    Accepts JSON body with optional keys:
    - 'opponent_types': ["FIRE", "WATER", ...] (tokens or raw strings)
    - 'opponent_sprites': ["pokemon_icon_025_00.png", ...] (server will extract ids)
    """
    payload = request.get_json(force=True, silent=True) or {}
    opp_types = payload.get('opponent_types')
    opp_sprites = payload.get('opponent_sprites')
    # derive types from sprites if provided
    derived = None
    if opp_sprites and isinstance(opp_sprites, list):
        derived = []
        from .pokemon import _extract_id_from_filename
        for s in opp_sprites:
            try:
                pid = _extract_id_from_filename(s)
                if pid is not None:
                    p = pokedex.get(pid)
                    if p and p.types:
                        derived.extend([t for t in (p.types or []) if t])
            except Exception:
                continue

    final_opp = None
    if opp_types:
        final_opp = opp_types
    elif derived:
        final_opp = derived

    try:
        box_user_id = payload.get('box_user_id')
        team = service.recommend_team(opponent_types=final_opp, box_user_id=box_user_id)
        return jsonify(team=team)
    except Exception as e:
        return jsonify(error=str(e)), 500


# --- Authentication endpoints (JWT access + refresh tokens) ---
def _create_access_token(uid: str):
    now = datetime.datetime.utcnow()
    exp = now + datetime.timedelta(seconds=cfg.ACCESS_TOKEN_EXP)
    payload = { 'sub': uid, 'iat': int(now.timestamp()), 'exp': int(exp.timestamp()) }
    # Ensure the jwt module provides the expected API
    if not _JWT_HAS_ENCODE:
        # Provide a helpful runtime error so the developer can fix their env
        raise RuntimeError(
            f"JWT encode function not available. Install PyJWT (pip install PyJWT) "
            f"or remove any local module named 'jwt'. Detected module path: {_JWT_MODULE_PATH}"
        )
    token = jwt.encode(payload, cfg.JWT_SECRET, algorithm='HS256')
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token


@app.route('/api/v1/signup', methods=['POST'])
def signup():
    payload = request.get_json(force=True, silent=True) or {}
    username = payload.get('username')
    password = payload.get('password')
    if not username or not password:
        return jsonify(error='username and password required'), 400
    username = str(username).strip()
    try:
        existing = None
        try:
            existing = repo.get_user(username)
        except Exception:
            existing = None
        if existing and existing.password_hash:
            return jsonify(error='User already exists'), 400
        pw_hash = generate_password_hash(password)
        repo.set_user_password(username, pw_hash)
        return jsonify(created=True, id=username, message='Account created')
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/api/v1/login', methods=['POST'])
def login():
    payload = request.get_json(force=True, silent=True) or {}
    username = payload.get('username')
    password = payload.get('password')
    if not username or not password:
        return jsonify(error='username and password required'), 400
    try:
        user = repo.get_user(username)
        if not user or not user.password_hash:
            return jsonify(error='Invalid credentials'), 401
        if not check_password_hash(user.password_hash, password):
            return jsonify(error='Invalid credentials'), 401
        try:
            access = _create_access_token(username)
        except RuntimeError as re:
            # return a helpful server error for misconfigured environments
            return jsonify(error=str(re)), 500
        refresh = uuid.uuid4().hex
        repo.create_refresh_token(username, refresh)
        return jsonify(access_token=access, refresh_token=refresh)
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/api/v1/refresh', methods=['POST'])
def refresh_token():
    payload = request.get_json(force=True, silent=True) or {}
    token = payload.get('refresh_token')
    if not token:
        return jsonify(error='refresh_token required'), 400
    try:
        rt = repo.get_refresh_token(token)
        if not rt or getattr(rt, 'revoked', False):
            return jsonify(error='Invalid refresh token'), 401
        uid = rt.user_id
        new_refresh = uuid.uuid4().hex
        repo.revoke_refresh_token(token)
        repo.create_refresh_token(uid, new_refresh)
        access = _create_access_token(uid)
        return jsonify(access_token=access, refresh_token=new_refresh)
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/api/v1/logout', methods=['POST'])
def logout():
    payload = request.get_json(force=True, silent=True) or {}
    token = payload.get('refresh_token')
    if not token:
        return jsonify(error='refresh_token required'), 400
    try:
        ok = repo.revoke_refresh_token(token)
        return jsonify(revoked=bool(ok))
    except Exception as e:
        return jsonify(error=str(e)), 500

