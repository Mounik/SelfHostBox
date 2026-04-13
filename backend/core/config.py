import os
from pathlib import Path

import yaml


_config = None

DEFAULTS = {
    "version": "1.0",
    "base_domain": "selfhostbox.local",
    "traefik_network": "selfhostbox",
    "ssl": {
        "enabled": True,
        "email": "admin@example.com",
        "provider": "letsencrypt",
        "staging": False,
    },
    "storage": {
        "data_dir": "/opt/selfhostbox/data",
        "backups_dir": "/opt/selfhostbox/backups",
    },
    "backup": {
        "enabled": True,
        "schedule": "0 2 * * *",
        "retention_days": 7,
    },
    "updates": {
        "enabled": True,
        "check_interval": "24h",
        "auto_apply": False,
    },
    "apps_dir": "/opt/selfhostbox/apps",
    "database": {
        "type": "sqlite",
        "path": "/opt/selfhostbox/selfhostbox.db",
    },
    "auth": {
        "secret_key": "change-me-in-production",
        "token_expiry_hours": 24,
    },
}


def _get_config_paths():
    paths = []
    env_path = os.environ.get("SELFHOSTBOX_CONFIG")
    if env_path:
        paths.append(Path(env_path))
    paths.append(Path("/opt/selfhostbox/config/config.yml"))
    paths.append(Path(__file__).parent.parent.parent / "config" / "config.yml")
    paths.append(Path(__file__).parent.parent.parent / "config" / "config.yml.example")
    return paths


def _deep_merge(base, override):
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config():
    global _config
    if _config is not None:
        return _config

    config = DEFAULTS.copy()
    for config_path in _get_config_paths():
        if config_path.exists():
            with open(config_path) as f:
                file_config = yaml.safe_load(f) or {}
            config = _deep_merge(config, file_config)
            break

    _config = config
    return _config


def get_config():
    return load_config()


def get_database_uri():
    config = get_config()
    db_config = config.get("database", {})
    if db_config.get("type") == "sqlite":
        return f"sqlite:///{db_config.get('path', '/opt/selfhostbox/selfhostbox.db')}"
    if db_config.get("type") == "postgresql":
        return db_config.get("uri", "postgresql://localhost/selfhostbox")
    return "sqlite:////opt/selfhostbox/selfhostbox.db"
