from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(String(64), primary_key=True)
    # store a password hash for credential-based login (nullable for service accounts)
    password_hash = Column(String(255), nullable=True)


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


class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'
    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(String(64), ForeignKey('users.id'), index=True)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship('User', backref='refresh_tokens')
