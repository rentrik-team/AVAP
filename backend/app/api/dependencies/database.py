"""Re-export database dependency for cleaner imports in routes."""

from app.database.session import get_db

__all__ = ["get_db"]
