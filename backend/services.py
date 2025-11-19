import os
from typing import Any, List, Tuple, Optional

from .dto import BoxEntry


class BoxService:
    """Service layer providing business logic around box operations.

    Keeps validation and simple domain rules here so the Flask handlers
    remain thin.
    """

    def __init__(self, repo: Any, assets_dir: str, pokedex: Optional[Any] = None):
        self.repo = repo
        self.assets_dir = assets_dir
        # optional Pokedex instance (from backend.pokemon.Pokedex)
        self.pokedex = pokedex

    def get_box(self, user_id: str) -> List[dict]:
        return [e.to_dict() for e in self.repo.get_box(user_id)]

    def add_to_box(self, user_id: str, name: str, sprite: str, cp, quick_move=None, charge_moves=None):
        # Name (nickname) is optional. If not provided, we'll store None and
        # display the species name in the UI.
        # (Keep validation light here — frontend controls whether a nickname
        # is provided.)

        # Require CP to be provided
        if cp is None:
            raise ValueError('CP is required')
        # Validate cp value
        try:
            cp = int(cp)
            if cp < 0:
                raise ValueError()
        except Exception:
            raise ValueError('Invalid cp value')

        # Validate sprite if local filename
        is_url = isinstance(sprite, str) and (sprite.startswith('http://') or sprite.startswith('https://'))
        if not is_url:
            candidate = os.path.join(self.assets_dir, sprite)
            if not os.path.exists(candidate):
                raise FileNotFoundError('Sprite not found in assets')

        # If we have a pokedex loaded, attempt to validate provided moves
        # Determine a poke_id from the sprite filename when possible.
        try:
            from .pokemon import _extract_id_from_filename
        except Exception:
            _extract_id_from_filename = None

        poke_id = None
        if isinstance(sprite, str) and _extract_id_from_filename is not None:
            try:
                poke_id = _extract_id_from_filename(sprite)
            except Exception:
                poke_id = None

        # Normalize charge_moves input early (allow None, string or list)
        if isinstance(charge_moves, str):
            ch_moves = [charge_moves]
        else:
            ch_moves = list(charge_moves or [])

        if poke_id is not None and getattr(self, 'pokedex', None) is not None:
            p = self.pokedex.get(poke_id)
            # only validate if we have an indexed pokedex entry
            if p is not None:
                # helper to extract move names from possibly-object lists
                def _move_names(arr):
                    try:
                        return [ (m if isinstance(m, str) else (m.get('name') or '')) for m in (arr or []) ]
                    except Exception:
                        return []

                # If the pokedex lists quick moves, require a quick_move be selected
                if p.quick_moves and len(p.quick_moves) > 0:
                    allowed_q = _move_names(p.quick_moves)
                    if not quick_move:
                        raise ValueError(f"A quick move must be provided for poke_id {poke_id}")
                    if quick_move not in allowed_q:
                        raise ValueError(f"quick_move '{quick_move}' is not valid for poke_id {poke_id}")

                # If the pokedex lists charge moves, require at least one and validate
                if p.charge_moves and len(p.charge_moves) > 0:
                    allowed_c = _move_names(p.charge_moves)
                    if len(ch_moves) < 1:
                        raise ValueError(f"At least one charge move must be provided for poke_id {poke_id}")

                # Enforce max 2 charge moves
                if len(ch_moves) > 2:
                    raise ValueError('At most 2 charge moves may be selected')

                # Validate each charge move is known for this Pokemon
                for cm in ch_moves:
                    if cm and cm not in allowed_c:
                        raise ValueError(f"charge_move '{cm}' is not valid for poke_id {poke_id}")

        # Build DTO with normalized charge moves
        entry = BoxEntry(name=name, sprite=sprite, cp=cp,
                         quick_move=quick_move, charge_moves=ch_moves or [])
        return [e.to_dict() for e in self.repo.add_entry(user_id, entry)]

    def remove_from_box(self, user_id: str, slot: int) -> Tuple[dict, List[dict]]:
        removed, box = self.repo.remove_entry(user_id, slot)
        return removed.to_dict(), [e.to_dict() for e in box]

    def update_entry(self, user_id: str, slot: int, name: str, sprite: str, cp, quick_move=None, charge_moves=None):
        """Update an existing box entry at `slot` with the provided values.

        Validation mirrors add_to_box (CP, sprite existence, move validation).
        """
        # Require CP to be provided
        if cp is None:
            raise ValueError('CP is required')
        # Validate cp value
        try:
            cp = int(cp)
            if cp < 0:
                raise ValueError()
        except Exception:
            raise ValueError('Invalid cp value')

        # Validate sprite if local filename
        is_url = isinstance(sprite, str) and (sprite.startswith('http://') or sprite.startswith('https://'))
        if not is_url:
            candidate = os.path.join(self.assets_dir, sprite)
            if not os.path.exists(candidate):
                raise FileNotFoundError('Sprite not found in assets')

        # attempt to derive poke id for move validation
        try:
            from .pokemon import _extract_id_from_filename
        except Exception:
            _extract_id_from_filename = None

        poke_id = None
        if isinstance(sprite, str) and _extract_id_from_filename is not None:
            try:
                poke_id = _extract_id_from_filename(sprite)
            except Exception:
                poke_id = None

        # Normalize charge_moves input early (allow None, string or list)
        if isinstance(charge_moves, str):
            ch_moves = [charge_moves]
        else:
            ch_moves = list(charge_moves or [])

        if poke_id is not None and getattr(self, 'pokedex', None) is not None:
            p = self.pokedex.get(poke_id)
            if p is not None:
                # helper to extract move names from possibly-object lists
                def _move_names(arr):
                    try:
                        return [ (m if isinstance(m, str) else (m.get('name') or '')) for m in (arr or []) ]
                    except Exception:
                        return []

                if p.quick_moves and len(p.quick_moves) > 0:
                    allowed_q = _move_names(p.quick_moves)
                    if not quick_move:
                        raise ValueError(f"A quick move must be provided for poke_id {poke_id}")
                    if quick_move not in allowed_q:
                        raise ValueError(f"quick_move '{quick_move}' is not valid for poke_id {poke_id}")

                if p.charge_moves and len(p.charge_moves) > 0:
                    allowed_c = _move_names(p.charge_moves)
                    if len(ch_moves) < 1:
                        raise ValueError(f"At least one charge move must be provided for poke_id {poke_id}")

                if len(ch_moves) > 2:
                    raise ValueError('At most 2 charge moves may be selected')

                for cm in ch_moves:
                    if cm and cm not in allowed_c:
                        raise ValueError(f"charge_move '{cm}' is not valid for poke_id {poke_id}")

        entry = BoxEntry(name=name, sprite=sprite, cp=cp,
                         quick_move=quick_move, charge_moves=ch_moves or [])
        # delegate update to repo
        return [e.to_dict() for e in self.repo.update_entry(user_id, slot, entry)]
