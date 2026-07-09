"""Centralized application configuration.

All configuration originates from environment variables.
The application fails at startup if required variables are missing.
"""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AVAP"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # Database
    database_url: str | None = None
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "avap"
    postgres_user: str = "avap_user"
    postgres_password: str = "changeme"

    # Scanner
    nmap_executable: str = "/usr/bin/nmap"
    scan_timeout: int = 300
    openvas_host: str = "localhost"
    openvas_port: int = 9390
    openvas_username: str = "admin"
    openvas_password: str = "changeme"

    # AI Providers
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-4o"
    groq_api_key: str = ""
    gemini_api_key: str = ""
    huggingface_api_key: str = ""

    # Reporting
    report_output_directory: str = "./generated_reports"

    # Logging
    log_level: str = "INFO"
    log_directory: str = "./logs"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Validate that log level is a recognized Python logging level."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_value = value.upper()
        if upper_value not in allowed:
            raise ValueError(
                f"Invalid log level: {value}. Allowed: {', '.join(sorted(allowed))}"
            )
        return upper_value

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        """Validate environment name."""
        allowed = {"development", "staging", "production", "testing"}
        lower_value = value.lower()
        if lower_value not in allowed:
            raise ValueError(
                f"Invalid environment: {value}. "
                f"Allowed: {', '.join(sorted(allowed))}"
            )
        return lower_value

    @property
    def effective_database_url(self) -> str:
        """Return the database URL, constructing from parts if not provided."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def log_directory_path(self) -> Path:
        """Return the log directory as a Path object."""
        return Path(self.log_directory)

    @property
    def report_output_path(self) -> Path:
        """Return the report output directory as a Path object."""
        return Path(self.report_output_directory)


def get_settings() -> Settings:
    """Create and return application settings.

    Settings are loaded from environment variables and .env file.
    This function creates a new instance each time to support testing.
    """
    return Settings()
