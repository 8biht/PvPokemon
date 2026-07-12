"""Command handlers that perform write-side actions and publish domain events.

These wrap the existing service layer operations and emit simple events
that projections can subscribe to. This keeps existing service logic but
adds an EDA step so read-models can react to changes.
"""
from typing import Any, Dict
from . import event_bus
from . import kafka_adapter


def handle_add_to_box(service, user_id: str, name: str, sprite: str, cp, quick_move=None, charge_moves=None):
    """Perform add command using service and publish Box.EntryAdded event."""
    box = service.add_to_box(user_id, name, sprite, cp, quick_move=quick_move, charge_moves=charge_moves)
    # the service returns the new box list; craft a small event payload
    payload = { 'user_id': user_id, 'action': 'add', 'entry_snapshot': box[-1] if box else None, 'box': box }
    try:
        event_bus.bus.publish('Box.EntryAdded', payload)
        try:
            kafka_adapter.publish('Box.EntryAdded', payload)
        except Exception:
            pass
    except Exception:
        pass
    return box


def handle_update_box_entry(service, user_id: str, slot: int, name: str, sprite: str, cp, quick_move=None, charge_moves=None):
    """Perform update command and publish Box.EntryUpdated event."""
    box = service.update_entry(user_id, slot, name, sprite, cp, quick_move=quick_move, charge_moves=charge_moves)
    payload = { 'user_id': user_id, 'action': 'update', 'slot': slot, 'box': box }
    try:
        event_bus.bus.publish('Box.EntryUpdated', payload)
        try:
            kafka_adapter.publish('Box.EntryUpdated', payload)
        except Exception:
            pass
    except Exception:
        pass
    return box


def handle_remove_from_box(service, user_id: str, slot: int):
    """Perform remove command and publish Box.EntryRemoved event."""
    removed, box = service.remove_from_box(user_id, slot)
    payload = { 'user_id': user_id, 'action': 'remove', 'removed': removed, 'box': box, 'slot': slot }
    try:
        event_bus.bus.publish('Box.EntryRemoved', payload)
        try:
            kafka_adapter.publish('Box.EntryRemoved', payload)
        except Exception:
            pass
    except Exception:
        pass
    return removed, box
