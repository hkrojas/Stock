from flask import Flask, session

from config import Config
from app.extensions import login_manager
from app.models import User


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(_user_id):
        from app.utils.api_client import APIClient

        token = session.get("access_token")
        if not token:
            return None

        # Check for cached user data in the session
        user_data = session.get("user_data")
        if user_data:
            return User(user_data)

        try:
            user_data = APIClient(token=token).get("/auth/me")
            if user_data:
                # Cache the dict in session for subsequent requests
                # Convert list of objects to list of dicts if necessary (role assigned_buildings)
                session["user_data"] = user_data
                return User(user_data)
            return None
        except Exception:
            session.pop("access_token", None)
            session.pop("user_data", None)
            return None

    from app.blueprints.auth import auth_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.catalog import catalog_bp
    from app.blueprints.orders import orders_bp
    from app.blueprints.dispatch import dispatch_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(catalog_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(dispatch_bp)

    @app.context_processor
    def inject_now():
        from datetime import datetime, timezone

        return {
            "now": datetime.now(timezone.utc),
            "api_docs_url": app.config.get("API_DOCS_URL"),
        }

    @app.template_filter("zfill")
    def zfill_filter(value, width):
        return str(value).zfill(width)

    return app
