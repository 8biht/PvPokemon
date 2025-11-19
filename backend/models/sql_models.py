from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(String(64), primary_key=True)


class BoxEntry(Base):
    __tablename__ = 'box_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), ForeignKey('users.id'), index=True)
    name = Column(String(200))
    sprite = Column(String(400))
    cp = Column(Integer, nullable=True)
    quick_move = Column(String(200), nullable=True)
    # store one or multiple charge moves as a comma-separated string
    charge_move = Column(String(400), nullable=True)

    user = relationship('User', backref='box_entries')
