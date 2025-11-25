"""Simple projection handlers that update read-model snapshots in response to events.

This demonstrates an event-driven read-side update: when box events occur
we write a JSON snapshot per user to `backend/data/read_models/box_{user}.json`.
In production the projection would update a dedicated read-optimized store.
"""
import json
import os
from typing import Any, Dict

from . import event_bus


READ_MODELS_DIR = os.path.join(os.path.dirname(__file__), 'data', 'read_models')
os.makedirs(READ_MODELS_DIR, exist_ok=True)


def _write_user_box_snapshot(user_id: str, box_data: Any):
    path = os.path.join(READ_MODELS_DIR, f'box_{user_id}.json')
    try:
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump({'user_id': user_id, 'box': box_data}, fh, indent=2)
    except Exception as e:
        print(f"[projections] failed to write snapshot for {user_id}: {e}")


def _on_entry_added(payload: Dict[str, Any]):
    try:
        user = payload.get('user_id')
        box = payload.get('box')
        _write_user_box_snapshot(user, box)
    except Exception as e:
        print('[projections] entry added handler error', e)


def _on_entry_updated(payload: Dict[str, Any]):
    try:
        user = payload.get('user_id')
        box = payload.get('box')
        _write_user_box_snapshot(user, box)
    except Exception as e:
        print('[projections] entry updated handler error', e)


def _on_entry_removed(payload: Dict[str, Any]):
    try:
        user = payload.get('user_id')
        box = payload.get('box')
        _write_user_box_snapshot(user, box)
    except Exception as e:
        print('[projections] entry removed handler error', e)


def register_default_projections():
    """Register the basic projections with the global event bus."""
    event_bus.bus.subscribe('Box.EntryAdded', _on_entry_added)
    event_bus.bus.subscribe('Box.EntryUpdated', _on_entry_updated)
    event_bus.bus.subscribe('Box.EntryRemoved', _on_entry_removed)
