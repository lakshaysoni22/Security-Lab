"""
LEATrace pytest configuration.

Sets up test environment:
- Forces SQLite file-based DB (overrides DATABASE_URL)
- Sets JWT_SECRET_KEY for tests
- Disables demo data and background tasks
- Uses checkfirst=True on create_all to prevent duplicate-table errors
  when multiple test modules import app.main
"""

import os
import pytest

# Must be set BEFORE any app module imports
os.environ["DATABASE_URL"] = "sqlite:///./test_leatrace.db"
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-only-for-tests-not-production-64chars!!")
os.environ.setdefault("LEATrace_DEMO_DATA", "false")
os.environ.setdefault("LEATrace_BACKGROUND_TASKS", "false")
os.environ.setdefault("LOG_FORMAT", "text")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("SANCTIONS_SOURCES", "")      # no live downloads in tests
os.environ.setdefault("TAXII_SERVER_URL", "")        # no live TAXII in tests
os.environ.setdefault("OAUTH_CLIENT_SECRET", "")     # no OAuth bootstrap in tests


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables before test session and drop after."""
    from app.database import engine, Base

    # checkfirst=True: safe to call multiple times across test modules
    Base.metadata.create_all(bind=engine, checkfirst=True)
    yield
    Base.metadata.drop_all(bind=engine)

    # Dispose all connections so Windows releases the file lock
    engine.dispose()
    import time as _time
    import os as _os
    _time.sleep(0.2)
    if _os.path.exists("test_leatrace.db"):
        try:
            _os.remove("test_leatrace.db")
        except PermissionError:
            pass  # Best-effort; CI will clean on next run


@pytest.fixture
def db_session(setup_test_db):
    """Returns a fresh DB session per test, rolls back after."""
    from app.database import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
