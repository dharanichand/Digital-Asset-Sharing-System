import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


def normalize_database_url(database_url: str) -> str:
    """Render/Heroku sometimes provide postgres://, but SQLAlchemy needs postgresql://."""
    if database_url and database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    return database_url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key")

    DATABASE_URL = normalize_database_url(os.environ.get("DATABASE_URL"))

    # Local fallback stays SQLite, but Render will use PostgreSQL through DATABASE_URL.
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or "sqlite:///" + os.path.join(BASE_DIR, "database.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-this-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    # Dynamic email / SMTP settings. For Gmail, use a Gmail App Password.
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["1", "true", "yes", "on"]
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() in ["1", "true", "yes", "on"]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

    PASSWORD_RESET_TOKEN_MAX_AGE = int(os.environ.get("PASSWORD_RESET_TOKEN_MAX_AGE", 1800))

