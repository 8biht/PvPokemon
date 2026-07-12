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

    def recommend_team(self, opponent_types: Optional[List[str]] = None, max_candidates: int = 50, box_user_id: Optional[str] = None) -> List[dict]:
        """Recommend a team of up to 3 Pokémon from the loaded pokedex.

        Simple heuristic-based recommender:
        - Scores each pokedex entry by estimated average move power, number of types,
          and how those types differ from the opponent types (if provided).
        - Examines top N candidates and returns the best 3-combination that maximizes
          combined score and type diversity.

        This is intentionally lightweight and deterministic; it provides a useful
        baseline for UI recommendations and can be improved later with a proper
        type-effectiveness matrix and move DPS estimates.
        """
        if getattr(self, 'pokedex', None) is None:
            return []

        # If box_user_id is provided, restrict candidates to entries in that user's box
        candidates_source = None
        if box_user_id:
            try:
                raw_entries = self.repo.get_box(box_user_id)
            except Exception:
                raw_entries = None
            if raw_entries:
                # Map raw box entries to pokedex Pokemon objects when possible
                candidates = []
                try:
                    from .pokemon import _extract_id_from_filename
                except Exception:
                    _extract_id_from_filename = None
                for be in raw_entries:
                    # be may be a DTO with .sprite attribute or a dict-like
                    sprite = None
                    try:
                        sprite = getattr(be, 'sprite', None) or (be.get('sprite') if isinstance(be, dict) else None)
                    except Exception:
                        sprite = None
                    pid = None
                    if sprite and _extract_id_from_filename:
                        try:
                            pid = _extract_id_from_filename(sprite)
                        except Exception:
                            pid = None
                    if pid is not None:
                        p = self.pokedex.get(pid)
                        if p is not None:
                            candidates.append((p, sprite))
                # If we found any candidates from the box, use them
                if candidates:
                    candidates_source = candidates

        # normalize opponent types
        opp_norm = None
        if opponent_types:
            opp_norm = [str(t).upper().replace('POKEMON_TYPE_', '').strip() for t in opponent_types if t]

        def _move_power(m: Any) -> float:
            try:
                if isinstance(m, dict):
                    # common keys: 'power' or 'damage'
                    return float(m.get('power') or m.get('damage') or 0)
            except Exception:
                return 0.0
            return 0.0

        # A compact type-effectiveness table (attacker -> defender -> multiplier).
        # This mirrors the frontend chart so recommendations can consider actual
        # effectiveness vs selected opponent types. Values are simplified.
        TYPE_EFFECTIVENESS = {
            'NORMAL': {'ROCK':0.5, 'GHOST':0, 'STEEL':0.5},
            'FIRE': {'GRASS':2, 'ICE':2, 'BUG':2, 'STEEL':2, 'FIRE':0.5, 'WATER':0.5, 'ROCK':0.5, 'DRAGON':0.5},
            'WATER': {'FIRE':2, 'GROUND':2, 'ROCK':2, 'WATER':0.5, 'GRASS':0.5, 'DRAGON':0.5},
            'ELECTRIC': {'WATER':2, 'FLYING':2, 'ELECTRIC':0.5, 'GRASS':0.5, 'DRAGON':0.5, 'GROUND':0},
            'GRASS': {'WATER':2, 'GROUND':2, 'ROCK':2, 'FIRE':0.5, 'GRASS':0.5, 'POISON':0.5, 'FLYING':0.5, 'BUG':0.5, 'DRAGON':0.5, 'STEEL':0.5},
            'ICE': {'GRASS':2, 'GROUND':2, 'FLYING':2, 'DRAGON':2, 'FIRE':0.5, 'WATER':0.5, 'ICE':0.5, 'STEEL':0.5},
            'FIGHTING': {'NORMAL':2, 'ICE':2, 'ROCK':2, 'DARK':2, 'STEEL':2, 'POISON':0.5, 'FLYING':0.5, 'PSYCHIC':0.5, 'BUG':0.5, 'FAIRY':0.5},
            'POISON': {'GRASS':2, 'FAIRY':2, 'POISON':0.5, 'GROUND':0.5, 'ROCK':0.5, 'GHOST':0.5, 'STEEL':0},
            'GROUND': {'FIRE':2, 'ELECTRIC':2, 'POISON':2, 'ROCK':2, 'STEEL':2, 'GRASS':0.5, 'BUG':0.5, 'FLYING':0},
            'FLYING': {'GRASS':2, 'FIGHTING':2, 'BUG':2, 'ELECTRIC':0.5, 'ROCK':0.5, 'STEEL':0.5},
            'PSYCHIC': {'FIGHTING':2, 'POISON':2, 'PSYCHIC':0.5, 'STEEL':0.5, 'DARK':0},
            'BUG': {'GRASS':2, 'PSYCHIC':2, 'DARK':2, 'FIRE':0.5, 'FIGHTING':0.5, 'POISON':0.5, 'FLYING':0.5, 'GHOST':0.5, 'STEEL':0.5, 'FAIRY':0.5},
            'ROCK': {'FIRE':2, 'ICE':2, 'FLYING':2, 'BUG':2, 'FIGHTING':0.5, 'GROUND':0.5, 'STEEL':0.5},
            'GHOST': {'PSYCHIC':2, 'GHOST':2, 'NORMAL':0, 'DARK':0.5},
            'DRAGON': {'DRAGON':2, 'STEEL':0.5, 'FAIRY':0},
            'DARK': {'PSYCHIC':2, 'GHOST':2, 'FIGHTING':0.5, 'DARK':0.5, 'FAIRY':0.5},
            'STEEL': {'ICE':2, 'ROCK':2, 'FAIRY':2, 'FIRE':0.5, 'WATER':0.5, 'ELECTRIC':0.5, 'STEEL':0.5},
            'FAIRY': {'FIGHTING':2, 'DRAGON':2, 'DARK':2, 'FIRE':0.5, 'POISON':0.5, 'STEEL':0.5}
        }

        scored = []
        # If we have a candidates_source (from user's box), use that, otherwise use full pokedex
        if candidates_source is not None:
            iterator = [(p, sprite) for (p, sprite) in candidates_source]
        else:
            iterator = [(p, (p.sprites[0] if getattr(p, 'sprites', None) else None)) for p in self.pokedex.all()]

        for p, spr in iterator:
            types = [str(t).upper() for t in (p.types or [])]

            # compute average move power from available move objects when present
            powers = []
            for m in (p.charge_moves or []) + (p.quick_moves or []):
                pw = _move_power(m)
                if pw and pw > 0:
                    powers.append(pw)
            avg_power = (sum(powers) / len(powers)) if powers else 8.0

            # prefer types that are different from opponent types (simple proxy for coverage)
            diff_score = 0
            if opp_norm:
                for t in types:
                    if t and t not in opp_norm:
                        diff_score += 1

            # compute effectiveness score against opponent types using the TYPE_EFFECTIVENESS table
            eff_score = 0.0
            if opp_norm and types:
                for opp in opp_norm:
                    # for this opponent defender type, find best multiplier from any of the attacker's types
                    best_mult = 1.0
                    for at in types:
                        try:
                            mult = TYPE_EFFECTIVENESS.get(at, {}).get(opp, 1.0)
                        except Exception:
                            mult = 1.0
                        if mult > best_mult:
                            best_mult = mult
                    # sum contributions (multiplier above 1 contributes positive coverage)
                    eff_score += (best_mult - 1.0)

            # base score: avg power + small bonus for type count and diff
            # add a larger weight for effectiveness so opponent types influence selection
            score = avg_power + (len(types) * 1.5) + (diff_score * 2.0) + (eff_score * 25.0)
            # keep sprite context when available by storing tuple (score, p, sprite)
            scored.append((score, p, spr))

        # consider top candidates by score
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:max_candidates]

        # brute-force best 3-combination by combined score + diversity bonus
        from itertools import combinations

        best_combo = None
        best_value = -1e9
        DEF_WEIGHT = 20.0
        for combo in combinations(top, min(3, len(top))):
            combo_pokes = [c[1] for c in combo]
            combo_score = sum(c[0] for c in combo)
            # diversity = number of distinct types across team
            all_types = set(t for p in combo_pokes for t in (p.types or []))
            diversity_bonus = len(all_types) * 4.0

            # compute defensive vulnerability against the provided opponent types
            vulnerability = 1.0
            if opp_norm and len(opp_norm) > 0:
                vul_sum = 0.0
                for opp in opp_norm:
                    member_mults = []
                    for mem in combo_pokes:
                        mem_types = [str(t).upper() for t in (mem.types or [])]
                        if not mem_types:
                            mem_types = ['NORMAL']
                        mult = 1.0
                        for dt in mem_types:
                            try:
                                mult *= TYPE_EFFECTIVENESS.get(opp, {}).get(dt, 1.0)
                            except Exception:
                                mult *= 1.0
                        member_mults.append(mult)
                    vul_sum += (sum(member_mults) / len(member_mults)) if member_mults else 1.0
                vulnerability = vul_sum / len(opp_norm)

            # final value: offense + diversity - defensive penalty
            penalty = (vulnerability - 1.0) * DEF_WEIGHT
            value = combo_score + diversity_bonus - penalty
            if value > best_value:
                best_value = value
                # track corresponding sprites as well
                best_combo = [(c[1], c[2]) for c in combo]

        if not best_combo:
            return []

        # transform to simple dicts, include a selected quick/charge move (highest power if available)
        def _select_best_moves(p: Any, sprite_hint: Optional[str] = None) -> dict:
            best_charge = None
            best_q = None
            # select highest-power charge move if objects available
            for m in (p.charge_moves or []):
                if isinstance(m, dict) and ('power' in m or 'damage' in m):
                    if best_charge is None or _move_power(m) > _move_power(best_charge):
                        best_charge = m
            for m in (p.quick_moves or []):
                if isinstance(m, dict) and ('power' in m or 'damage' in m):
                    if best_q is None or _move_power(m) > _move_power(best_q):
                        best_q = m
            # resolve sprite: prefer provided hint, then pokedex sprites, then try common asset filename pattern
            final_sprite = None
            if sprite_hint:
                final_sprite = sprite_hint
            else:
                try:
                    if getattr(p, 'sprites', None) and len(p.sprites) > 0:
                        final_sprite = p.sprites[0]
                except Exception:
                    final_sprite = None

            # fallback: construct a common asset filename pattern (e.g. pokemon_icon_025_00.png)
            if not final_sprite and getattr(self, 'assets_dir', None):
                try:
                    cand = f"pokemon_icon_{int(p.poke_id):03d}_00.png"
                    full = os.path.join(self.assets_dir, cand)
                    if os.path.exists(full):
                        final_sprite = cand
                except Exception:
                    final_sprite = None

            return {
                'poke_id': p.poke_id,
                'name': p.name,
                'types': p.types,
                'sprite': final_sprite,
                'quick_move': (best_q if best_q is not None else (p.quick_moves[0] if p.quick_moves else None)),
                'charge_move': (best_charge if best_charge is not None else (p.charge_moves[0] if p.charge_moves else None)),
            }

        # best_combo now contains list of (Pokemon, sprite) pairs
        return [_select_best_moves(p, sprite_hint=spr) for (p, spr) in best_combo]
