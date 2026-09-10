import asyncio
import sys
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import String
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api import deps as api_deps
from app.config.config import settings
from app.db.session import get_db as db_session_get_db
from app.main import app
from app.models.base import Base


# Replace Geometry column types with String columns for SQLite.
# This is done at conftest import time before the test session runs.
def _patch_geometry_columns():
    from geoalchemy2 import Geometry

    for table in list(Base.metadata.tables.values()):
        for column in list(table.columns):
            if isinstance(column.type, Geometry):
                column.type = String(2048)


_patch_geometry_columns()


TEST_DATABASE_URI = "sqlite+aiosqlite:///:memory:"


engine_test = create_async_engine(TEST_DATABASE_URI, echo=False)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine_test, class_=AsyncSession
)


async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


async def _create_tables() -> None:
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def _drop_tables() -> None:
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def _prepare_database():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(_create_tables())
    yield
    loop.run_until_complete(_drop_tables())
    loop.close()


app.dependency_overrides[db_session_get_db] = _override_get_db
app.dependency_overrides[api_deps.get_db] = _override_get_db


@pytest_asyncio.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables():
    async with engine_test.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    yield
