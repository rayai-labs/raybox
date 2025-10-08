"""Database connection management for Raybox API."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import asyncpg
from asyncpg.pool import PoolConnectionProxy


class Database:
    """Manages asyncpg connection pool.

    Uses Supabase connection pooler (port 6543) for efficient connection management.
    Supabase provides PgBouncer pooling in transaction mode, and we add an
    application-level pool for connection reuse within the FastAPI app.
    """

    def __init__(self):
        """Initialize database manager."""
        self.pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Initialize connection pool.

        Expects SUPABASE_DB_URL environment variable pointing to the pooler:
        postgresql://postgres:password@aws-0-us-west-1.pooler.supabase.com:6543/postgres

        Note: Use port 6543 (pooler) not port 5432 (direct connection).
        """
        db_url = os.environ.get("SUPABASE_DB_URL")
        if not db_url:
            raise ValueError("SUPABASE_DB_URL environment variable is required")

        # Validate that we're using the pooler (port 6543)
        if ":5432/" in db_url:
            raise ValueError(
                "SUPABASE_DB_URL should use the pooler connection (port 6543), "
                "not direct connection (port 5432). "
                "Use: postgresql://...pooler.supabase.com:6543/postgres"
            )

        self.pool = await asyncpg.create_pool(
            db_url,
            min_size=5,
            max_size=20,
            command_timeout=60,
        )

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[PoolConnectionProxy[asyncpg.Record], None]:
        """Get a connection from the pool.

        Usage:
            async with db.connection() as conn:
                querier = AsyncQuerier(conn)
                result = await querier.get_api_key_by_hash(key_hash)
        """
        if not self.pool:
            raise RuntimeError("Database pool not initialized. Call connect() first.")

        async with self.pool.acquire() as conn:
            yield conn


# Global database instance
db = Database()
