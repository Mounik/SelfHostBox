"""SelfHostBox — Web UI for self-hosted apps"""

import logging
import os

from flask import Flask
from flask_cors import CORS

from backend.core.config import get_config, get_database_uri
from backend.models import db
from backend.api.routes import (
    register_auth_routes,
    register_app_routes,
    register_store_routes,
    register_system_routes,
)


def create_app(config_override=None):
    app = Flask(
        __name__,
        template_folder="../frontend",
        static_folder="../frontend/static",
    )

    config = get_config()

    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get(
        "SELFHOSTBOX_SECRET_KEY",
        config.get("auth", {}).get("secret_key", "change-me-in-production"),
    )
    app.config["BASE_DOMAIN"] = config.get("base_domain", "selfhostbox.local")

    if config_override:
        app.config.update(config_override)

    CORS(app, origins=config.get("cors_origins", ["http://localhost:8080"]))

    db.init_app(app)

    with app.app_context():
        db.create_all()

    register_auth_routes(app)
    register_app_routes(app)
    register_store_routes(app)
    register_system_routes(app)

    @app.route("/")
    def index():
        from flask import render_template

        return render_template("index.html")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=8080)
