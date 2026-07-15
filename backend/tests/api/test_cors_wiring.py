from app.main import create_app


def _cors_kwargs(app):
    """Return the kwargs the app was configured with for CORSMiddleware."""
    for middleware in app.user_middleware:
        if middleware.cls.__name__ == "CORSMiddleware":
            return middleware.kwargs
    raise AssertionError("CORSMiddleware was not registered on the app")


def test_create_app_wires_cors_allowed_origins_from_settings(monkeypatch):
    """The application factory must read the configured allowlist rather
    than hardcoding a wildcard, so the separately-deployed frontend origin
    is the only one ever allowed in production.
    """
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS", "https://app.example.com,https://staging.example.com"
    )

    app = create_app()

    kwargs = _cors_kwargs(app)
    assert kwargs["allow_origins"] == [
        "https://app.example.com",
        "https://staging.example.com",
    ]
    assert kwargs["allow_credentials"] is False


def test_create_app_default_cors_allows_local_frontend_dev_origin(monkeypatch):
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)

    app = create_app()

    kwargs = _cors_kwargs(app)
    assert kwargs["allow_origins"] == ["http://localhost:3000"]
