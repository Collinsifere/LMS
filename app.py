import os
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
from sqlalchemy import text

from models import db, User

# Load environment variables early
load_dotenv()


def create_app(config_object: str | None = None) -> Flask:
    """
    Application factory.
    - Uses DATABASE_URL by default (PostgreSQL)
    - Supports optional config object import path (e.g., 'config.DevelopmentConfig')
    """
    app = Flask(__name__)

    # ------------------------------------------------
    # Core Configuration
    # ------------------------------------------------
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # Prefer DATABASE_URL. If someone sets DEV_DATABASE_URL, fall back to that.
    database_url = os.getenv("DATABASE_URL") or os.getenv("DEV_DATABASE_URL")

    # Safe default for local dev (psycopg v3 driver)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "postgresql+psycopg://postgres:password@localhost:5432/lms_db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Upload settings
    app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "uploads")
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16MB default
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Optional: allow loading a config object if you later adopt config.py
    # Example: create_app("config.DevelopmentConfig")
    if config_object:
        module_path, obj_name = config_object.rsplit(".", 1)
        module = __import__(module_path, fromlist=[obj_name])
        app.config.from_object(getattr(module, obj_name))

    # ------------------------------------------------
    # Initialize extensions
    # ------------------------------------------------
    db.init_app(app)

    # ------------------------------------------------
    # Flask-Login setup
    # ------------------------------------------------
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id: str):
        # UUID-safe load (SQLAlchemy 2.x)
        return db.session.get(User, user_id)

    # ------------------------------------------------
    # Register blueprints
    # ------------------------------------------------
    from routes.home import home_bp
    from routes.auth import auth_bp
    from routes.courses import courses_bp
    from routes.dashboard import dashboard_bp
    from routes.assignments import assignments_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(courses_bp, url_prefix="/courses")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(assignments_bp, url_prefix="/assignments")

    # ------------------------------------------------
    # Initialize Database + Optional pgvector extension
    # ------------------------------------------------
    with app.app_context():
        try:
            # Create tables first
            db.create_all()

            # Enable pgvector if present on server
            # Note: pg_available_extensions lists extensions that can be installed.
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
                print("AI vector extension enabled (pgvector).")
            else:
                db.session.rollback()
                print("pgvector not available on this PostgreSQL server (skipping).")

            print("Database connected successfully.")
            print("Tables created/verified.")

        except Exception as e:
            db.session.rollback()
            print("Database initialization failed:")
            print(e)

    return app


if __name__ == "__main__":
    # Debug should come from FLASK_ENV/your config, but keeping your behavior:
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", "5000")))