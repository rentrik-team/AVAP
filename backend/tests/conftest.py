import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import all models so Base.metadata registers every table for create_all.
# This must happen before `from app.main import app` below: `import app.models`
# binds the top-level `app` package name in this module's namespace, which
# would otherwise shadow the FastAPI `app` instance imported next.
import app.models  # noqa: F401
from app.api.dependencies.database import get_db
from app.database.base import Base
from app.main import app

# SQLite database URL for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# Create test engine using StaticPool to maintain state in memory
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def db_engine():
    """Create database schema for tests."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Provide a transactional scope around a series of operations.

    Uses a SAVEPOINT (nested transaction) so that application code calling
    session.commit() (as production services do) commits only the savepoint,
    never the outer transaction. Without this, a service's session.commit()
    would end the outer transaction directly on this shared connection, and
    any later session.rollback() (e.g. an error-handling rollback further
    into the same test) would discard all prior "committed" data instead of
    only the failed operation's own uncommitted work. The final teardown
    rollback still discards everything, keeping tests isolated.
    """
    connection = db_engine.connect()
    # Begin a non-ORM transaction
    transaction = connection.begin()
    # Bind an individual Session to the connection
    session = TestingSessionLocal(bind=connection)

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    # Rollback - everything that happened with the Session above
    # is rolled back, leaving the DB clean
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Provide a FastAPI TestClient with the database dependency overridden."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Transaction rollback handles cleanup

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
