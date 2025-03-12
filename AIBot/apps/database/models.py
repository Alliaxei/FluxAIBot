from datetime import datetime

from sqlalchemy import BIGINT, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, relationship, validates
from sqlalchemy.orm import mapped_column

from apps.database.database import Base, engine
from sqlalchemy import String
from sqlalchemy import func

TRANSACTION_TYPES = ('recharge', 'spend', 'refund')
TRANSACTION_STATUSES = ('pending', 'paid', 'failed')

TRANSACTION_TOKEN_TYPES = ('spend_tokens', 'earn_tokens')
class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id = mapped_column(BIGINT)
    first_name: Mapped[str] = mapped_column(String(50), nullable=True)
    username: Mapped[str] = mapped_column(String(50), nullable=True)
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    transactions = relationship('Transaction', back_populates='user', cascade='all, delete-orphan')

    token_transactions = relationship('TokenTransaction', back_populates='user', cascade='all, delete-orphan')

    settings = relationship('UserSettings', back_populates='user', uselist=False,  cascade='all, delete-orphan')

    gallery = relationship('Gallery', back_populates='user',  cascade='all, delete-orphan')

class Transaction(Base):
    __tablename__ = 'transactions'

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    amount: Mapped[int] = mapped_column()
    transaction_date: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    transaction_type: Mapped[str] = mapped_column(String(15), nullable=False)
    transaction_status: Mapped[str] = mapped_column(String(15), nullable=True)
    credits_amount: Mapped[int] = mapped_column(nullable=True)
    credits_added: Mapped[bool] = mapped_column(default=False, nullable=True)

    user = relationship('User', back_populates='transactions')

    @validates("transaction_type")
    def validate_transaction_type(self, key, value):
        if value not in TRANSACTION_TYPES:
            raise ValueError(f"Invalid transaction type: {value}")
        return value

    @validates("transaction_status")
    def validate_transaction_type(self, key, value):
        if value not in TRANSACTION_STATUSES:
            raise ValueError(f"Invalid transaction status: {value}")
        return value

class TokenTransaction(Base):
    __tablename__ = 'token_transactions'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='Cascade'), nullable=False)
    amount: Mapped[int] = mapped_column()
    transaction_date: Mapped[datetime] = mapped_column(DateTime)
    transaction_type: Mapped[str] = mapped_column(String(15), nullable=False)

    user = relationship('User', back_populates='token_transactions')
    @validates("transaction_type")
    def validate_transaction_type(self, key, value):
        if value not in TRANSACTION_TOKEN_TYPES:
            raise ValueError(f"Invalid transaction type: {value}")
        return value
class UserSettings(Base):
    __tablename__ = 'settings'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id:  Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    selected_style: Mapped[str] = mapped_column(String(50), nullable=True, default='schnell')
    image_size: Mapped[str] = mapped_column(String(30), nullable=True, default='512x512')

    user = relationship('User', back_populates='settings')

class Gallery(Base):
    __tablename__ = 'gallery'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[BIGINT] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'))
    image_path: Mapped[str] = mapped_column(String, nullable=True)
    image_url: Mapped[str] = mapped_column(String, nullable=True)
    prompt: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=True)
    user = relationship('User', back_populates='gallery')

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
