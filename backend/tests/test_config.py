from app.core.config import Settings


def test_settings_defaults():
    settings = Settings()
    assert settings.PROJECT_NAME == "InternPilot AI API"
    assert settings.VERSION == "0.1.0"
    assert settings.BACKEND_PORT == 8000
    assert "postgresql+asyncpg" in settings.DATABASE_URL
    assert "redis://" in settings.REDIS_URL


def test_cors_origins_parsing():
    settings = Settings(BACKEND_CORS_ORIGINS="http://localhost:3000, https://internpilot.ai")
    assert "http://localhost:3000" in settings.BACKEND_CORS_ORIGINS
    assert "https://internpilot.ai" in settings.BACKEND_CORS_ORIGINS


def test_cors_origins_json_list():
    settings = Settings(BACKEND_CORS_ORIGINS='["http://localhost:3000", "http://localhost:8080"]')
    assert len(settings.BACKEND_CORS_ORIGINS) == 2
    assert "http://localhost:8080" in settings.BACKEND_CORS_ORIGINS
