import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import get_settings


class JSONFormatter(logging.Formatter):
    """Custom formatter to output structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as a JSON string."""
        log_obj: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Add extra context if passed via 'extra' dictionary
        if hasattr(record, "context"):
            log_obj["context"] = getattr(record, "context")

        return json.dumps(log_obj)


def setup_logging() -> None:
    """Configure structured logging for the application.
    
    Sets up JSON formatting to stdout and optionally to a file if configured.
    """
    settings = get_settings()

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()

    # JSON Formatter
    formatter = JSONFormatter()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File Handler (Optional, based on config)
    if settings.log_directory:
        log_dir = settings.log_directory_path
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # We could use a RotatingFileHandler here for production
        log_file = log_dir / "avap.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Reduce noise from chatty third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
