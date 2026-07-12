from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class BoxEntry:
    name: Optional[str]
    sprite: str
    cp: Optional[int] = None
    quick_move: Optional[str] = None
    charge_moves: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        # include both 'charge_moves' (array) and legacy 'charge_move' (first element) for compatibility
        legacy_charge = self.charge_moves[0] if self.charge_moves else None
        return {
            "name": self.name,
            "sprite": self.sprite,
            "cp": self.cp,
            "quick_move": self.quick_move,
            "charge_moves": self.charge_moves,
            "charge_move": legacy_charge,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> 'BoxEntry':
        charge = d.get('charge_moves') or ([] if d.get('charge_move') is None else [d.get('charge_move')])
        return BoxEntry(
            name=d.get('name'),
            sprite=d.get('sprite'),
            cp=d.get('cp'),
            quick_move=d.get('quick_move'),
            charge_moves=list(charge),
        )
