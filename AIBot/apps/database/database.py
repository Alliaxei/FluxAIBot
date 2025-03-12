from dotenv import load_dotenv
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, AsyncSession

import os

load_dotenv('.env')

DATABASE_URL = os.getenv("SQL_ALCHEMY_URL")

engine = create_async_engine(os.getenv('SQL_ALCHEMY_URL'))

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(AsyncAttrs, DeclarativeBase):
    pass