from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

# Simple file-based persistence for boxes (Pokemon GO style). Replace with a DB in production.
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
BOXES_FILE = os.path.join(DATA_DIR, 'boxes.json')

# Path to the bundled sprite assets in the repository
ASSETS_DIR = os.path.join(BASE_DIR, 'PokeMiners pogo_assets master Images-Pokemon - 256x256')

os.makedirs(DATA_DIR, exist_ok=True)


def _load_boxes():
    if not os.path.exists(BOXES_FILE):
        return {}
    try:
        with open(BOXES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_boxes(data):
    with open(BOXES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


@app.route('/')
def index():
    return jsonify(message="Welcome to PokeApp Backend")


@app.route('/ping')
def ping():
    return jsonify(message="pong")


@app.route('/api/v1/sprites')
def list_sprites():
    """Return a list of available sprite filenames (limited to first 500)."""
    if not os.path.isdir(ASSETS_DIR):
        return jsonify(error="Assets folder not found"), 500
    files = [f for f in os.listdir(ASSETS_DIR) if f.lower().endswith('.png')]
    files.sort()
    return jsonify(sprites=files)


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
    boxes = _load_boxes()
    return jsonify(box=boxes.get(user_id, []))


@app.route('/api/v1/box/<string:user_id>', methods=['POST'])
def add_to_box(user_id):
    """Add a Pokemon to a user's box (Pokemon GO style).

    Expected JSON: { "name": "Pikachu", "sprite": "pokemon_icon_025_00.png", "cp": 523 }
    The sprite may be a filename present in the assets folder or an absolute URL.
    """
    payload = request.get_json(force=True, silent=True)
    if not payload:
        return jsonify(error='Invalid JSON body'), 400
    name = payload.get('name')
    sprite = payload.get('sprite')
    cp = payload.get('cp')
    if not name:
        return jsonify(error='Missing name'), 400
    if not sprite:
        return jsonify(error='Missing sprite'), 400

    # Validate cp if provided
    if cp is not None:
        try:
            cp = int(cp)
            if cp < 0:
                raise ValueError()
        except Exception:
            return jsonify(error='Invalid cp value'), 400

    is_url = isinstance(sprite, str) and (sprite.startswith('http://') or sprite.startswith('https://'))
    if not is_url:
        candidate = os.path.join(ASSETS_DIR, sprite)
        if not os.path.exists(candidate):
            return jsonify(error='Sprite not found in assets', sprite=sprite), 400

    boxes = _load_boxes()
    user_box = boxes.get(user_id, [])

    entry = {'name': name, 'sprite': sprite, 'cp': cp}
    user_box.append(entry)
    boxes[user_id] = user_box
    _save_boxes(boxes)
    return jsonify(box=user_box)


@app.route('/api/v1/box/<string:user_id>/<int:slot>', methods=['DELETE'])
def remove_from_box(user_id, slot):
    boxes = _load_boxes()
    user_box = boxes.get(user_id, [])
    if slot < 0 or slot >= len(user_box):
        return jsonify(error='Invalid slot index'), 400
    removed = user_box.pop(slot)
    boxes[user_id] = user_box
    _save_boxes(boxes)
    return jsonify(removed=removed, box=user_box)


if __name__ == '__main__':
    app.run(debug=True)

