import json
import hashlib
import secrets as _secrets
from datetime import datetime, timezone

from flask import request, jsonify
from flask_sqlalchemy import SQLAlchemy

from backend.models import db, DeployedApp
from backend.core.auth import require_auth, generate_token, verify_token
from backend.core.docker import deploy, start, stop, remove, get_logs, list_templates


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = hashlib.sha256(
            password.encode() + b"selfhostbox-salt"
        ).hexdigest()

    def check_password(self, password):
        return (
            self.password_hash
            == hashlib.sha256(password.encode() + b"selfhostbox-salt").hexdigest()
        )


def register_auth_routes(app):
    @app.route("/api/auth/setup", methods=["POST"])
    def setup_admin():
        if User.query.first() is not None:
            return jsonify({"error": "Admin already exists"}), 409
        data = request.json
        username = data.get("username", "admin")
        password = data.get("password")
        if not password or len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        token = generate_token(user.id, user.username)
        return jsonify({"token": token, "username": user.username}), 201

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        data = request.json
        username = data.get("username", "")
        password = data.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            return jsonify({"error": "Invalid credentials"}), 401
        token = generate_token(user.id, user.username)
        return jsonify({"token": token, "username": user.username})

    @app.route("/api/auth/check", methods=["GET"])
    def auth_check():
        has_admin = User.query.first() is not None
        return jsonify({"setup_required": not has_admin})

    @app.route("/api/auth/me", methods=["GET"])
    @require_auth
    def me():
        return jsonify(
            {
                "user_id": request.current_user["user_id"],
                "username": request.current_user["username"],
            }
        )


def register_app_routes(app):
    @app.route("/api/apps")
    @require_auth
    def list_apps():
        apps = DeployedApp.query.all()
        return jsonify([a.to_dict() for a in apps])

    @app.route("/api/apps", methods=["POST"])
    @require_auth
    def create_app():
        data = request.json
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        app_type = data.get("app_type", "")
        name = data.get("name", f"{app_type}-{_secrets.token_hex(4)}")
        domain = data.get(
            "domain", f"{name}.{app.config.get('BASE_DOMAIN', 'selfhostbox.local')}"
        )
        env_vars = data.get("env_vars", {})

        success, error = deploy(app_type, name, domain, env_vars)
        if not success:
            return jsonify({"error": error}), 400

        deployed = DeployedApp(
            name=name,
            app_type=app_type,
            domain=domain,
            status="running",
            env_vars=json.dumps(sanitize_env_vars(env_vars) or {}),
            volumes=json.dumps([]),
        )
        db.session.add(deployed)
        db.session.commit()
        return jsonify(deployed.to_dict()), 201

    @app.route("/api/apps/<int:app_id>", methods=["GET"])
    @require_auth
    def get_app(app_id):
        deployed_app = DeployedApp.query.get_or_404(app_id)
        return jsonify(deployed_app.to_dict())

    @app.route("/api/apps/<int:app_id>", methods=["DELETE"])
    @require_auth
    def delete_app(app_id):
        deployed_app = DeployedApp.query.get_or_404(app_id)
        success, error = remove(deployed_app.name)
        db.session.delete(deployed_app)
        db.session.commit()
        return jsonify({"status": "deleted"})

    @app.route("/api/apps/<int:app_id>/start", methods=["POST"])
    @require_auth
    def start_app(app_id):
        deployed_app = DeployedApp.query.get_or_404(app_id)
        success, error = start(deployed_app.name)
        if not success:
            return jsonify({"error": error}), 500
        deployed_app.status = "running"
        db.session.commit()
        return jsonify(deployed_app.to_dict())

    @app.route("/api/apps/<int:app_id>/stop", methods=["POST"])
    @require_auth
    def stop_app(app_id):
        deployed_app = DeployedApp.query.get_or_404(app_id)
        success, error = stop(deployed_app.name)
        if not success:
            return jsonify({"error": error}), 500
        deployed_app.status = "stopped"
        db.session.commit()
        return jsonify(deployed_app.to_dict())

    @app.route("/api/apps/<int:app_id>/restart", methods=["POST"])
    @require_auth
    def restart_app(app_id):
        deployed_app = DeployedApp.query.get_or_404(app_id)
        stop(deployed_app.name)
        success, error = start(deployed_app.name)
        if not success:
            return jsonify({"error": error}), 500
        deployed_app.status = "running"
        db.session.commit()
        return jsonify(deployed_app.to_dict())

    @app.route("/api/apps/<int:app_id>/logs", methods=["GET"])
    @require_auth
    def app_logs(app_id):
        deployed_app = DeployedApp.query.get_or_404(app_id)
        tail = request.args.get("tail", 100, type=int)
        logs = get_logs(deployed_app.name, tail=tail)
        if logs is None:
            return jsonify({"error": "Could not retrieve logs"}), 500
        return jsonify({"logs": logs})


def register_store_routes(app):
    @app.route("/api/store")
    @require_auth
    def list_store():
        apps = list_templates()
        return jsonify(apps)


def register_system_routes(app):
    @app.route("/api/system/info")
    @require_auth
    def system_info():
        import psutil

        return jsonify(
            {
                "cpu_percent": psutil.cpu_percent(),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent,
                },
                "disk": {
                    "total": psutil.disk_usage("/").total,
                    "free": psutil.disk_usage("/").free,
                    "percent": psutil.disk_usage("/").percent,
                },
            }
        )

    @app.route("/api/system/health")
    def health_check():
        return jsonify({"status": "ok"}), 200


def sanitize_env_vars(env_vars):
    from backend.core.validators import sanitize_env_vars as _sev

    return _sev(env_vars)
