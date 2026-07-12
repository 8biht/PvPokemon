from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
import json
import os
import re


@dataclass
class Pokemon:
    """Domain model for a Pokemon (Pokemon GO oriented).

    Fields:
    - poke_id: integer pokemon-go id (e.g. 25 for Pikachu)
    - name: optional display name
    - types: list of type names (e.g. ['electric'])
    - quick_moves: list of quick move names
    - charge_moves: list of charge move names
    - sprites: list of sprite filenames (relative to assets dir)
    """

    poke_id: int
    name: Optional[str] = None
    types: List[str] = field(default_factory=list)
    # quick_moves / charge_moves can be either a list of move-name strings
    # or a list of move objects like {name, power, type} depending on the
    # source data. Keep them as-is so we preserve metadata when available.
    quick_moves: List[Union[str, Dict[str, Any]]] = field(default_factory=list)
    charge_moves: List[Union[str, Dict[str, Any]]] = field(default_factory=list)
    sprites: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "poke_id": self.poke_id,
            "name": self.name,
            "types": self.types,
            # expose move objects when available (or strings when not)
            "quick_moves": self.quick_moves,
            "charge_moves": self.charge_moves,
            "sprites": self.sprites,
        }

    @staticmethod
    def from_dict(d: Dict) -> 'Pokemon':
        return Pokemon(
            poke_id=int(d.get('poke_id')),
            name=d.get('name'),
            types=list(d.get('types') or []),
            # preserve move objects when present; fall back to names
            quick_moves=list(d.get('quick_moves') or []),
            charge_moves=list(d.get('charge_moves') or []),
            sprites=list(d.get('sprites') or []),
        )


_FIRST_NUMBER = re.compile(r"(\d+)")


def _extract_id_from_filename(filename: str) -> Optional[int]:
    """Extract the first sequence of digits from a filename and return as int.

    Example: 'pokemon_icon_025_00.png' -> 25
    """
    m = _FIRST_NUMBER.search(filename)
    if not m:
        return None
    try:
        # Some names may contain leading zeros, int handles that
        return int(m.group(1))
    except Exception:
        return None


def _normalize_type_token(t: Any) -> Optional[str]:
    """Normalize various type token shapes into a canonical upper-case short form.

    Examples:
      'POKEMON_TYPE_FIRE' -> 'FIRE'
      'fire' -> 'FIRE'
      None -> None
    """
    if not t:
        return None
    try:
        s = str(t).upper()
        # remove common prefix
        s = re.sub(r'^POKEMON_TYPE_', '', s)
        s = s.strip()
        return s
    except Exception:
        return None


def build_catalog_from_assets(assets_dir: str) -> Dict[int, Pokemon]:
    """Scan `assets_dir` for PNG files, group them by the leading ID in filename,
    and return a dict mapping poke_id -> Pokemon (with sprites populated).

    The function does not attempt to populate moves/types/name — those can be
    loaded from an external dataset and merged into the catalog later.
    """
    catalog: Dict[int, Pokemon] = {}
    if not os.path.isdir(assets_dir):
        return catalog

    for fname in os.listdir(assets_dir):
        if not fname.lower().endswith('.png'):
            continue
        pid = _extract_id_from_filename(fname)
        if pid is None:
            continue
        if pid not in catalog:
            catalog[pid] = Pokemon(poke_id=pid)
        catalog[pid].sprites.append(fname)

    # Optional: sort sprite lists for deterministic ordering
    for p in catalog.values():
        p.sprites.sort()

    return catalog


class Pokedex:
    """Simple in-memory registry for Pokemon objects.

    You can construct one from an assets folder with `Pokedex.from_assets()`
    then merge additional metadata (names, moves, types) from another source.
    """

    def __init__(self):
        self._by_id: Dict[int, Pokemon] = {}

    def add(self, p: Pokemon):
        self._by_id[p.poke_id] = p

    def get(self, poke_id: int) -> Optional[Pokemon]:
        return self._by_id.get(poke_id)

    def all(self) -> List[Pokemon]:
        return list(self._by_id.values())

    @classmethod
    def from_assets(cls, assets_dir: str) -> 'Pokedex':
        pk = cls()
        catalog = build_catalog_from_assets(assets_dir)
        for p in catalog.values():
            pk.add(p)
        return pk

    @classmethod
    def from_file(cls, path: str) -> 'Pokedex':
        """Load a pokedex file from JSON.

        This function supports two cases:
        - file contains a list/array of pokemon entries -> those will be indexed by `dexNr` if present
        - file contains arbitrary JSON (e.g. an OpenAPI spec) -> stored as raw_data and
          a small sample extraction may be available under `pokedex_sample` key.
        """
        pk = cls()
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            return pk
        except Exception:
            return pk

        pk._raw_data = data  # keep raw for /raw endpoint

        # If data is a list of entries, try to index them. Support several possible
        # shapes: older export used keys like `dexNr`/`dex`, our consolidated file
        # uses `poke_id`, and move lists may be under `quick_moves`/`charge_moves`.
        if isinstance(data, list):
            for entry in data:
                # support multiple possible id keys
                dex = entry.get('dexNr') or entry.get('dex') or entry.get('dex_nr') or entry.get('poke_id') or entry.get('id')
                try:
                    dex_i = int(dex) if dex is not None else None
                except Exception:
                    dex_i = None
                if dex_i is not None:
                    # name: prefer canonical 'name' or nested names English
                    name = None
                    if isinstance(entry.get('names'), dict):
                        name = entry.get('names').get('English')
                    if not name:
                        name = entry.get('name')

                    # types: try multiple shapes and normalize tokens
                    types = []
                    if entry.get('types') and isinstance(entry.get('types'), list):
                        # values may be like 'GRASS' or 'POKEMON_TYPE_GRASS'
                        raw_types = entry.get('types')
                        types = [t for t in ([_normalize_type_token(x) for x in raw_types] if raw_types else []) if t]
                    elif entry.get('primaryType') and isinstance(entry.get('primaryType'), dict):
                        t = (entry.get('primaryType') or {}).get('type')
                        if t:
                            nt = _normalize_type_token(t)
                            types = [nt] if nt else []

                    # quick moves: preserve list of move objects when available
                    quick_moves = []
                    if entry.get('quick_moves') and isinstance(entry.get('quick_moves'), list):
                        # keep objects (dicts) or strings as-is, but normalize move.type when present
                        for m in entry.get('quick_moves'):
                            if isinstance(m, dict):
                                mm = dict(m)
                                if 'type' in mm:
                                    mm['type'] = _normalize_type_token(mm.get('type'))
                                quick_moves.append(mm)
                            elif isinstance(m, str):
                                quick_moves.append(m)
                    elif isinstance(entry.get('quickMoves'), dict):
                        # older shape: dict of {name: {...}} -> keep keys
                        quick_moves = list(entry.get('quickMoves').keys())

                    # charge moves: preserve list of objects when available
                    charge_moves = []
                    if entry.get('charge_moves') and isinstance(entry.get('charge_moves'), list):
                        for m in entry.get('charge_moves'):
                            if isinstance(m, dict):
                                mm = dict(m)
                                if 'type' in mm:
                                    mm['type'] = _normalize_type_token(mm.get('type'))
                                charge_moves.append(mm)
                            elif isinstance(m, str):
                                charge_moves.append(m)
                    elif isinstance(entry.get('cinematicMoves'), dict):
                        charge_moves = list(entry.get('cinematicMoves').keys())

                    p = Pokemon(poke_id=dex_i,
                                name=name,
                                types=types,
                                quick_moves=quick_moves,
                                charge_moves=charge_moves,
                                sprites=[])
                    pk.add(p)
        # If file has a 'pokedex_sample' array (our placeholder) use that
        elif isinstance(data, dict) and 'pokedex_sample' in data and isinstance(data['pokedex_sample'], list):
            for entry in data['pokedex_sample']:
                dex = entry.get('dexNr') or entry.get('dex') or entry.get('poke_id')
                try:
                    dex_i = int(dex) if dex is not None else None
                except Exception:
                    dex_i = None
                if dex_i is None:
                    # skip entries without numeric dex
                    continue

                name = None
                if isinstance(entry.get('names'), dict):
                    name = entry.get('names').get('English')
                if not name:
                    name = entry.get('name')

                types = []
                if entry.get('types') and isinstance(entry.get('types'), list):
                    raw_types = entry.get('types')
                    types = [t for t in ([_normalize_type_token(x) for x in raw_types] if raw_types else []) if t]
                elif entry.get('primaryType') and isinstance(entry.get('primaryType'), dict):
                    t = (entry.get('primaryType') or {}).get('type')
                    if t:
                        nt = _normalize_type_token(t)
                        types = [nt] if nt else []

                quick_moves = []
                if entry.get('quick_moves') and isinstance(entry.get('quick_moves'), list):
                    for m in entry.get('quick_moves'):
                        if isinstance(m, dict):
                            mm = dict(m)
                            if 'type' in mm:
                                mm['type'] = _normalize_type_token(mm.get('type'))
                            quick_moves.append(mm)
                        elif isinstance(m, str):
                            quick_moves.append(m)
                elif isinstance(entry.get('quickMoves'), dict):
                    quick_moves = list(entry.get('quickMoves').keys())

                charge_moves = []
                if entry.get('charge_moves') and isinstance(entry.get('charge_moves'), list):
                    for m in entry.get('charge_moves'):
                        if isinstance(m, dict):
                            mm = dict(m)
                            if 'type' in mm:
                                mm['type'] = _normalize_type_token(mm.get('type'))
                            charge_moves.append(mm)
                        elif isinstance(m, str):
                            charge_moves.append(m)
                elif isinstance(entry.get('cinematicMoves'), dict):
                    charge_moves = list(entry.get('cinematicMoves').keys())

                p = Pokemon(poke_id=dex_i,
                            name=name,
                            types=types,
                            quick_moves=quick_moves,
                            charge_moves=charge_moves,
                            sprites=[])
                if p.poke_id is not None:
                    pk.add(p)

        return pk

    def raw(self) -> Any:
        """Return raw loaded JSON (if any)."""
        return getattr(self, '_raw_data', None)
