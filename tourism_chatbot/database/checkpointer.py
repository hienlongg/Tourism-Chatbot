"""
PostgreSQL checkpointer initialization for LangGraph agents
"""

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import ConnectionPool, AsyncConnectionPool
import logging

logger = logging.getLogger(__name__)


def initialize_checkpointer(pool: ConnectionPool, setup_schema: bool = True) -> PostgresSaver:
    """
    Initialize PostgreSQL checkpointer for agent memory (sync version).
    
    This creates a PostgresSaver that stores conversation state in PostgreSQL.
    
    Args:
        pool: PostgreSQL connection pool
        setup_schema: If True, create required tables (checkpoints, checkpoint_writes)
    
    Returns:
        PostgresSaver: Configured checkpointer instance
    
    Example:
        >>> pool = get_connection_pool()
        >>> checkpointer = initialize_checkpointer(pool)
        >>> agent = create_react_agent(model, tools, checkpointer=checkpointer)
    """
    logger.info("Initializing PostgreSQL checkpointer (sync)...")
    
    checkpointer = PostgresSaver(pool)
    
    if setup_schema:
        logger.info("Setting up database schema (creating tables if not exist)...")
        checkpointer.setup()
        logger.info("Schema setup completed")
    
    logger.info("Checkpointer initialized successfully")
    
    return checkpointer


async def initialize_async_checkpointer(pool: AsyncConnectionPool, setup_schema: bool = True) -> AsyncPostgresSaver:
    """
    Initialize async PostgreSQL checkpointer for agent memory.
    
    This creates an AsyncPostgresSaver that stores conversation state in PostgreSQL.
    Use this version when using agent.astream() in async contexts like Chainlit.
    
    Args:
        pool: Async PostgreSQL connection pool
        setup_schema: If True, create required tables (checkpoints, checkpoint_writes)
    
    Returns:
        AsyncPostgresSaver: Configured async checkpointer instance
    
    Example:
        >>> pool = await get_async_connection_pool()
        >>> checkpointer = await initialize_async_checkpointer(pool)
        >>> agent = create_agent(model, tools, checkpointer=checkpointer)
    """
    logger.info("Initializing PostgreSQL checkpointer (async)...")
    
    checkpointer = AsyncPostgresSaver(pool)
    
    if setup_schema:
        logger.info("Setting up database schema (creating tables if not exist)...")
        await checkpointer.setup()
        logger.info("Schema setup completed")
    
    logger.info("Async checkpointer initialized successfully")
    
    return checkpointer
