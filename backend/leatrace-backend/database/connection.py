import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config.settings import settings
from shared.logger import logger

# --- 1. PostgreSQL / SQLAlchemy Configuration ---
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 2. MongoDB Configuration (NoSQL) ---
mongo_client = None
mongo_db = None

try:
    import pymongo
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    mongo_client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
    mongo_db = mongo_client[os.getenv("MONGO_DB_NAME", "LEAtTrace_nosql")]
except ImportError:
    logger.warning("pymongo not installed. Fallback to mock MongoDB client.")
except Exception as e:
    logger.error(f"Failed to configure MongoDB client: {e}")

class MockMongoCollection:
    def insert_one(self, document):
        logger.info(f"[Mock MongoDB Ingest]: {document}")
        return type('Obj', (object,), {'inserted_id': 'mock-id'})()

    def find_one(self, filter):
        return None

class MockMongoDB:
    def __getitem__(self, name):
        return MockMongoCollection()

def get_mongo_db():
    if mongo_db is not None:
        try:
            # Check connection
            mongo_client.server_info()
            return mongo_db
        except Exception:
            pass
    return MockMongoDB()

# --- 3. Redis Configuration (Caching) ---
redis_client = None

try:
    import redis
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    redis_client = redis.Redis(host=redis_host, port=redis_port, db=0, socket_timeout=2)
except ImportError:
    logger.warning("redis-py not installed. Fallback to mock Redis client.")
except Exception as e:
    logger.error(f"Failed to configure Redis client: {e}")

class MockRedis:
    def __init__(self):
        self.store = {}

    def set(self, key, value, ex=None):
        logger.info(f"[Mock Redis SET] {key} -> {value} (expiry: {ex})")
        self.store[key] = value
        return True

    def get(self, key):
        val = self.store.get(key)
        logger.info(f"[Mock Redis GET] {key} -> {val}")
        return val

    def expire(self, key, time):
        return True

def get_redis_client():
    if redis_client is not None:
        try:
            redis_client.ping()
            return redis_client
        except Exception:
            pass
    return MockRedis()
