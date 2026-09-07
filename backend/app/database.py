"""
LEATrace Database Configuration — Production.

Supports PostgreSQL (production default) and SQLite (development fallback).
Integrates with MongoDB for document storage and Redis for caching.

PRODUCTION INVARIANTS:
- No MockMongoDB or MockRedis classes. If a service is unavailable, return None.
- PostgreSQL is the recommended production database.
- Connection pool configured for concurrent access.
"""

import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import QueuePool

logger = logging.getLogger("leatrace.database")

# ===================================================================
# Primary SQL Database (PostgreSQL recommended, SQLite for dev)
# ===================================================================

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./LEATrace.db")

# Detect database type for engine configuration
_is_sqlite = DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    logger.warning(
        "Using SQLite database. This is suitable for development only. "
        "Set DATABASE_URL to a PostgreSQL connection string for production."
    )
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    # PostgreSQL with production connection pool settings
    engine = create_engine(
        DATABASE_URL,
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
        pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
        pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),
        pool_pre_ping=True,
        poolclass=QueuePool,
        echo=False,
    )
    logger.info(f"PostgreSQL engine initialized. Pool size: {engine.pool.size()}")


class Base(DeclarativeBase):
    """SQLAlchemy declarative base using modern API (replaces deprecated declarative_base())."""
    pass


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency for database sessions with automatic cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health() -> dict:
    """Returns database health status."""
    try:
        with engine.connect() as conn:
            conn.execute(engine.dialect.statement_compiler(engine.dialect, None).__class__("SELECT 1", None))
        return {"status": "healthy", "backend": "sqlite" if _is_sqlite else "postgresql"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)[:200]}


# ===================================================================
# MongoDB Configuration (Document store for AI logs, evidence docs)
# ===================================================================

_mongo_db = None
_mongo_client = None

try:
    import pymongo
    _mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    _mongo_client = pymongo.MongoClient(_mongo_url, serverSelectionTimeoutMS=3000)
    _mongo_db_name = os.getenv("MONGO_DB_NAME", "LEATrace_nosql")
    _mongo_db = _mongo_client[_mongo_db_name]
    # Verify connection
    _mongo_client.server_info()
    logger.info(f"MongoDB connected: {_mongo_db_name}")
except ImportError:
    logger.info("pymongo not installed. MongoDB features unavailable.")
except Exception as e:
    _mongo_db = None
    logger.info(f"MongoDB unavailable: {e}. Document features disabled.")


def get_mongo_db():
    """
    Returns the MongoDB database instance, or None if unavailable.
    Callers must handle None — no mock objects.
    """
    if _mongo_db is not None:
        try:
            _mongo_client.server_info()
            return _mongo_db
        except Exception:
            pass
    return None


# ===================================================================
# Redis Configuration (Caching, rate limiting, sessions)
# ===================================================================

redis_client = None

try:
    import redis as _redis_module
    _redis_host = os.getenv("REDIS_HOST", "localhost")
    _redis_port = int(os.getenv("REDIS_PORT", "6379"))
    _redis_password = os.getenv("REDIS_PASSWORD", "")

    redis_client = _redis_module.Redis(
        host=_redis_host,
        port=_redis_port,
        password=_redis_password if _redis_password else None,
        db=0,
        socket_timeout=1.0,
        socket_connect_timeout=1.0,
        decode_responses=True,
    )
    # Verify connection
    redis_client.ping()
    logger.info(f"Redis connected: {_redis_host}:{_redis_port}")
except ImportError:
    logger.info("redis package not installed. Caching features unavailable.")
except Exception as e:
    redis_client = None
    logger.info(f"Redis unavailable: {e}. Caching disabled.")


def get_redis_client():
    """
    Returns the Redis client, or None if unavailable.
    Callers must handle None — no mock objects.
    """
    if redis_client is not None:
        try:
            redis_client.ping()
            return redis_client
        except Exception:
            pass
    return None
