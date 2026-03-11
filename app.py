import importlib
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from sqlalchemy import text

from models import User, db

# Load environment variables as early as possible
load_dotenv()

# Flask extension instances
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_object: str | None = None) -> Flask:
    """
    Flask application factory.

    Responsibilities:
    - load configuration
    - initialize extensions
    - configure authentication
    - register blueprints
    - initialize optional database features
    """
    app = Flask(__name__)

    configure_app(app, config_object)
    initialize_extensions(app)
    configure_login_manager(app)
    register_blueprints(app)
    initialize_database_features(app)

    return app


def configure_app(app: Flask, config_object: str | None = None) -> None:
    """
    Configure the Flask app.
    """
    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "dev-secret-key-change-in-production",
    )

    database_url = os.getenv("DATABASE_URL") or os.getenv("DEV_DATABASE_URL")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        database_url or "postgresql+psycopg://postgres:password@localhost:5432/lms_db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    upload_folder = os.getenv("UPLOAD_FOLDER", "uploads")
    app.config["UPLOAD_FOLDER"] = str(Path(upload_folder))
    app.config["MAX_CONTENT_LENGTH"] = int(
        os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)
    )

    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    if config_object:
        module_path, object_name = config_object.rsplit(".", 1)
        module = importlib.import_module(module_path)
        app.config.from_object(getattr(module, object_name))


def initialize_extensions(app: Flask) -> None:
    """
    Initialize Flask extensions.
    """
    db.init_app(app)
    migrate.init_app(app, db)


def configure_login_manager(app: Flask) -> None:
    """
    Configure Flask-Login.
    """
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"
    login_manager.session_protection = "strong"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    """
    Load a user by primary key.
    UUID-safe because User.get_id() returns a string.
    """
    return db.session.get(User, user_id)


def register_blueprints(app: Flask) -> None:
    """
    Register application blueprints.
    """
    from routes.assignments import assignments_bp
    from routes.auth import auth_bp
    from routes.courses import courses_bp
    from routes.dashboard import dashboard_bp
    from routes.home import home_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(courses_bp, url_prefix="/courses")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(assignments_bp, url_prefix="/assignments")


def initialize_database_features(app: Flask) -> None:
    """
    Initialize optional database features.

    Notes:
    - This does NOT create tables.
    - Schema changes must be handled only through Flask-Migrate/Alembic.
    - pgvector is enabled only if available on the PostgreSQL server.
    - This step is skipped during migration commands to avoid side effects.
    """
    if should_skip_runtime_db_init():
        return

    with app.app_context():
        try:
            vector_available = db.session.execute(
                text(
                    """
                    SELECT 1
                    FROM pg_available_extensions
                    WHERE name = 'vector'
                    LIMIT 1
                    """
                )
            ).scalar()

            if vector_available:
                db.session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                db.session.commit()
                app.logger.info("AI vector extension enabled (pgvector).")
            else:
                db.session.rollback()
                app.logger.info(
                    "pgvector not available on this PostgreSQL server (skipping)."
                )

            db.session.execute(text("SELECT 1"))
            app.logger.info("Database connected successfully.")

        except Exception:
            db.session.rollback()
            app.logger.exception("Database initialization failed.")


def should_skip_runtime_db_init() -> bool:
    """
    Skip optional runtime DB initialization during migration commands
    or when explicitly disabled with FLASK_SKIP_DB_INIT=1.
    """
    if os.getenv("FLASK_SKIP_DB_INIT") == "1":
        return True

    command = " ".join(sys.argv).lower()
    migration_keywords = {
        "db",
        "migrate",
        "upgrade",
        "downgrade",
        "stamp",
        "history",
        "revision",
        "current",
        "heads",
        "branches",
        "merge",
        "show",
        "check",
    }

    return any(keyword in command for keyword in migration_keywords)


if __name__ == "__main__":
    app = create_app()
    app.run(
        debug=os.getenv("FLASK_ENV") == "development",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
    )
