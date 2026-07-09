from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Create SQLAlchemy engine
# pool_pre_ping=True helps handle dropped connections
engine = create_engine(
    settings.effective_database_url,
    pool_pre_ping=True,
    # Additional pool settings could be configured here for production
)

# Session factory for creating new database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency generator for database sessions.
    
    Yields a SQLAlchemy Session, ensuring it is closed after the request completes.
    Used for FastAPI dependency injection.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
