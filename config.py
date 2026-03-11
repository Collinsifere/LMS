import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def normalize_database_url(url: str | None) -> str | None:
    """
    Normalize database URLs from platforms like Heroku that use
    'postgres://' instead of 'postgresql://'.
    """
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


class Config:
    """Base configuration"""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }

    SESSION_COOKIE_HTTPONLY = True

    # File uploads
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))

    ALLOWED_EXTENSIONS = {
        "pdf",
        "doc",
        "docx",
        "txt",
        "zip",
        "jpg",
        "jpeg",
        "png",
    }

    # Sessions
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Pagination
    ITEMS_PER_PAGE = 20


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True

    SQLALCHEMY_DATABASE_URI = normalize_database_url(
        os.getenv(
            "DEV_DATABASE_URL",
            "postgresql+psycopg://postgres:password@localhost:5432/lms_db",
        )
    )


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False

    SQLALCHEMY_DATABASE_URI = normalize_database_url(os.getenv("DATABASE_URL"))

    if not SQLALCHEMY_DATABASE_URI:
        raise RuntimeError("DATABASE_URL must be set in production")

    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
