import asyncpg
from server.config import settings

connection_pool = None


async def init_db():
    global connection_pool
    try:
        connection_pool = await asyncpg.create_pool(
            dsn=settings.database_url,
        )
        await create_query_table()
        await create_pii_redaction_table()
    except Exception as e:
        import logging
        logging.warning(f"Database not available: {e}. Continuing without DB logging.")
        connection_pool = None


async def create_query_table():
    async with connection_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                """
                CREATE TABLE IF NOT EXISTS query_log (
                    id SERIAL PRIMARY KEY,
                    query TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    sources TEXT[],
                    estimated_input_tokens INTEGER,
                    estimated_output_tokens INTEGER,
                    estimated_cost FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )


async def create_pii_redaction_table():
    async with connection_pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute(
                """
                CREATE TABLE IF NOT EXISTS pii_redaction_log (
                    id SERIAL PRIMARY KEY,
                    query_hash TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    original_snippet TEXT,
                    redacted_snippet TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )


async def log_query(query: str, answer: str, sources: list, estimated_input_tokens: int = None, estimated_output_tokens: int = None, estimated_cost: float = None):
    if connection_pool is None:
        return  # DB not available, skip logging
    try:
        async with connection_pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    """
                    INSERT INTO query_log (query, answer, sources, estimated_input_tokens, estimated_output_tokens, estimated_cost)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    query,
                    answer,
                    sources,
                    estimated_input_tokens,
                    estimated_output_tokens,
                    estimated_cost,
                )
    except Exception as e:
        import logging
        logging.warning(f"Failed to log query: {e}")


async def log_pii_redaction(query_hash: str, entity_type: str, original_snippet: str, redacted_snippet: str):
    if connection_pool is None:
        return  # DB not available, skip logging
    try:
        async with connection_pool.acquire() as connection:
            async with connection.transaction():
                await connection.execute(
                    """
                    INSERT INTO pii_redaction_log (query_hash, entity_type, original_snippet, redacted_snippet)
                    VALUES ($1, $2, $3, $4)
                    """,
                    query_hash,
                    entity_type,
                    original_snippet,
                    redacted_snippet,
                )
    except Exception as e:
        import logging
        logging.warning(f"Failed to log PII redaction: {e}")


def estimate_tokens_and_cost(query: str, answer: str) -> tuple:
    estimated_input_tokens = len(query) / 4
    estimated_output_tokens = len(answer) / 4
    estimated_cost = (estimated_input_tokens / 1_000_000 * 0.59) + (estimated_output_tokens / 1_000_000 * 0.79)
    return estimated_input_tokens, estimated_output_tokens, estimated_cost
