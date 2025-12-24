"""
Database connection management for PostgreSQL
"""

import os
from typing import Optional
from psycopg_pool import ConnectionPool, AsyncConnectionPool
import logging

logger = logging.getLogger(__name__)


def get_db_uri() -> str:
    """
    Get PostgreSQL connection URI from environment variables.
    
    Returns:
        str: Database connection URI
    
    Raises:
        ValueError: If DATABASE_URL environment variable is missing
    """
    db_uri = os.getenv("DATABASE_URL")
    
    if not db_uri:
        raise ValueError("Missing required environment variable: DATABASE_URL")
    
    logger.info("Database URI retrieved from environment")
    
    return db_uri


def get_connection_pool(
    db_uri: Optional[str] = None,
    max_size: int = 10,
    min_size: int = 2
) -> ConnectionPool:
    """
    Create a PostgreSQL connection pool (sync version).
    
    Args:
        db_uri: Database connection URI (if None, built from env vars)
        max_size: Maximum number of connections in pool
        min_size: Minimum number of connections to maintain
    
    Returns:
        ConnectionPool: Configured connection pool
    """
    if db_uri is None:
        db_uri = get_db_uri()
    
    # Connection settings for LangGraph compatibility
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0  # Disable prepared statements
    }
    
    logger.info(f"Creating connection pool (min={min_size}, max={max_size})")
    
    pool = ConnectionPool(
        conninfo=db_uri,
        min_size=min_size,
        max_size=max_size,
        kwargs=connection_kwargs
    )
    
    logger.info("Connection pool created successfully")
    
    return pool


def get_async_connection_pool(
    db_uri: Optional[str] = None,
    max_size: int = 10,
    min_size: int = 2
) -> AsyncConnectionPool:
    """
    Create an async PostgreSQL connection pool.
    
    Use this for async contexts like Chainlit with agent.astream().
    
    Args:
        db_uri: Database connection URI (if None, built from env vars)
        max_size: Maximum number of connections in pool
        min_size: Minimum number of connections to maintain
    
    Returns:
        AsyncConnectionPool: Configured async connection pool
    """
    if db_uri is None:
        db_uri = get_db_uri()
    
    # Connection settings for LangGraph compatibility
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0  # Disable prepared statements
    }
    
    logger.info(f"Creating async connection pool (min={min_size}, max={max_size})")
    
    pool = AsyncConnectionPool(
        conninfo=db_uri,
        min_size=min_size,
        max_size=max_size,
        kwargs=connection_kwargs,
        open=False  # Don't open immediately, need to await open()
    )
    
    logger.info("Async connection pool created (call await pool.open() before use)")
    
    return pool
