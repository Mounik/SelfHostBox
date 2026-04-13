import json
import pytest
from backend.app import create_app
from backend.models import db as _db


@pytest.fixture
def app():
    app = create_app(
        config_override={
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "TESTING": True,
            "SECRET_KEY": "test-secret-key-for-tests",
        }
    )
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_token(client):
    res = client.post(
        "/api/auth/setup", json={"username": "admin", "password": "testpass123"}
    )
    assert res.status_code == 201
    data = res.get_json()
    return data["token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


class TestAuth:
    def test_setup_creates_admin(self, client):
        res = client.post(
            "/api/auth/setup", json={"username": "admin", "password": "testpass123"}
        )
        assert res.status_code == 201
        data = res.get_json()
        assert "token" in data
        assert data["username"] == "admin"

    def test_setup_twice_fails(self, client):
        client.post(
            "/api/auth/setup", json={"username": "admin", "password": "testpass123"}
        )
        res = client.post(
            "/api/auth/setup", json={"username": "admin2", "password": "testpass123"}
        )
        assert res.status_code == 409

    def test_setup_weak_password(self, client):
        res = client.post(
            "/api/auth/setup", json={"username": "admin", "password": "short"}
        )
        assert res.status_code == 400

    def test_login(self, client):
        client.post(
            "/api/auth/setup", json={"username": "admin", "password": "testpass123"}
        )
        res = client.post(
            "/api/auth/login", json={"username": "admin", "password": "testpass123"}
        )
        assert res.status_code == 200
        assert "token" in res.get_json()

    def test_login_wrong_password(self, client):
        client.post(
            "/api/auth/setup", json={"username": "admin", "password": "testpass123"}
        )
        res = client.post(
            "/api/auth/login", json={"username": "admin", "password": "wrongpass"}
        )
        assert res.status_code == 401

    def test_auth_check_no_admin(self, client):
        res = client.get("/api/auth/check")
        assert res.status_code == 200
        assert res.get_json()["setup_required"] is True

    def test_auth_check_with_admin(self, client, auth_token):
        res = client.get("/api/auth/check")
        assert res.status_code == 200
        assert res.get_json()["setup_required"] is False


class TestProtectedRoutes:
    def test_apps_requires_auth(self, client):
        res = client.get("/api/apps")
        assert res.status_code == 401

    def test_store_requires_auth(self, client):
        res = client.get("/api/store")
        assert res.status_code == 401

    def test_system_info_requires_auth(self, client):
        res = client.get("/api/system/info")
        assert res.status_code == 401

    def test_apps_with_auth(self, client, auth_headers):
        res = client.get("/api/apps", headers=auth_headers)
        assert res.status_code == 200

    def test_invalid_token(self, client):
        res = client.get("/api/apps", headers={"Authorization": "Bearer invalid"})
        assert res.status_code == 401


class TestHealthCheck:
    def test_health_no_auth(self, client):
        res = client.get("/api/system/health")
        assert res.status_code == 200
        assert res.get_json()["status"] == "ok"


class TestStore:
    def test_list_store(self, client, auth_headers):
        res = client.get("/api/store", headers=auth_headers)
        assert res.status_code == 200
        apps = res.get_json()
        assert isinstance(apps, list)
        app_ids = [a["id"] for a in apps]
        assert "portainer" in app_ids
        assert "nextcloud" in app_ids
        assert "vaultwarden" in app_ids
        assert "jellyfin" in app_ids


class TestValidators:
    def test_valid_app_names(self):
        from backend.core.validators import validate_app_name

        assert validate_app_name("my-app") is True
        assert validate_app_name("nextcloud-abc1") is True
        assert validate_app_name("ab") is False
        assert validate_app_name("UPPER") is False
        assert validate_app_name("app with spaces") is False
        assert validate_app_name("") is False
        assert validate_app_name(123) is False

    def test_valid_domains(self):
        from backend.core.validators import validate_domain

        assert validate_domain("example.com") is True
        assert validate_domain("app.example.com") is True
        assert validate_domain("my-app.domain.org") is True
        assert validate_domain("invalid") is False
        assert validate_domain("") is False
        assert validate_domain("has space.com") is False

    def test_valid_app_type(self):
        from backend.core.validators import validate_app_type

        assert validate_app_type("nextcloud") is True
        assert validate_app_type("uptime-kuma") is True
        assert validate_app_type("UPPER") is False
        assert validate_app_type("") is False

    def test_sanitize_env_vars(self):
        from backend.core.validators import sanitize_env_vars

        assert sanitize_env_vars({"KEY": "val"}) == {"KEY": "val"}
        assert sanitize_env_vars({"1BAD": "val"}) == {}
        assert sanitize_env_vars("not a dict") is None
        assert sanitize_env_vars({"GOOD_KEY": 123}) == {"GOOD_KEY": "123"}
