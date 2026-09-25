import os

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

engine = create_async_engine(os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/postgres'))

AsyncLocalSession = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncLocalSession() as session:
        yield session
