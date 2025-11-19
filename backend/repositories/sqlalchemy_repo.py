from typing import List, Tuple
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os

from ..models.sql_models import Base, User, BoxEntry as BoxEntryModel
from ..dto import BoxEntry


class SQLAlchemyBoxesRepository:
    """Repository implementation using SQLAlchemy and SQLite.

    The database URL is `sqlite:///backend/data/pvpokemon.db` by default.
    """

    def __init__(self, db_url: str = None):
        if db_url is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'pvpokemon.db')
            db_url = f'sqlite:///{os.path.abspath(db_path)}'
        self.engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def _session(self) -> Session:
        return self.SessionLocal()

    def get_box(self, user_id: str) -> List[BoxEntry]:
        with self._session() as s:
            entries = s.query(BoxEntryModel).filter(BoxEntryModel.user_id == user_id).order_by(BoxEntryModel.id).all()
            result = []
            for e in entries:
                # stored charge_move column may contain a comma-separated list
                ch_raw = e.charge_move or ''
                charge_moves = [c for c in (ch_raw.split(',') if ch_raw else []) if c]
                result.append(BoxEntry(name=e.name, sprite=e.sprite, cp=e.cp,
                                       quick_move=e.quick_move, charge_moves=charge_moves))
            return result

    def add_entry(self, user_id: str, entry: BoxEntry) -> List[BoxEntry]:
        with self._session() as s:
            user = s.get(User, user_id)
            if user is None:
                user = User(id=user_id)
                s.add(user)
                s.flush()
            # serialize charge_moves list into comma-separated string for storage
            ch_moves = getattr(entry, 'charge_moves', None)
            if ch_moves is None:
                ch_serial = None
            elif isinstance(ch_moves, list):
                ch_serial = ','.join([str(x) for x in ch_moves if x])
            else:
                ch_serial = str(ch_moves)

            model = BoxEntryModel(user_id=user_id, name=entry.name, sprite=entry.sprite, cp=entry.cp,
                                  quick_move=getattr(entry, 'quick_move', None),
                                  charge_move=ch_serial)
            s.add(model)
            s.commit()
            return self.get_box(user_id)

    def remove_entry(self, user_id: str, index: int) -> Tuple[BoxEntry, List[BoxEntry]]:
        with self._session() as s:
            entries = s.query(BoxEntryModel).filter(BoxEntryModel.user_id == user_id).order_by(BoxEntryModel.id).all()
            if index < 0 or index >= len(entries):
                raise IndexError('Invalid slot index')
            removed = entries[index]
            removed_data = BoxEntry(name=removed.name, sprite=removed.sprite, cp=removed.cp)
            s.delete(removed)
            s.commit()
            return removed_data, self.get_box(user_id)

    def update_entry(self, user_id: str, index: int, entry: BoxEntry) -> List[BoxEntry]:
        """Update an existing entry at `index` for `user_id` and return the updated box."""
        with self._session() as s:
            entries = s.query(BoxEntryModel).filter(BoxEntryModel.user_id == user_id).order_by(BoxEntryModel.id).all()
            if index < 0 or index >= len(entries):
                raise IndexError('Invalid slot index')
            model = entries[index]
            # update fields
            model.name = entry.name
            model.sprite = entry.sprite
            model.cp = entry.cp
            model.quick_move = getattr(entry, 'quick_move', None)
            ch_moves = getattr(entry, 'charge_moves', None)
            if ch_moves is None:
                model.charge_move = None
            elif isinstance(ch_moves, list):
                model.charge_move = ','.join([str(x) for x in ch_moves if x])
            else:
                model.charge_move = str(ch_moves)
            s.add(model)
            s.commit()
            return self.get_box(user_id)
