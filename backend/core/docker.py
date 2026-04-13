import json
import logging
import subprocess
import shutil
from pathlib import Path

from backend.core.config import get_config
from backend.core.validators import (
    validate_app_name,
    validate_domain,
    validate_app_type,
    sanitize_env_vars,
)

logger = logging.getLogger(__name__)

DOCKER_COMPOSE_CMD = "docker"


def _get_apps_dir():
    config = get_config()
    return Path(config.get("apps_dir", "/opt/selfhostbox/apps"))


def _get_templates_dir():
    return Path(__file__).parent.parent / "templates" / "apps"


def deploy(app_type, name, domain, env_vars=None):
    if not validate_app_type(app_type):
        return False, "Invalid app type"
    if not validate_app_name(name):
        return (
            False,
            "Invalid app name. Use lowercase alphanumeric with hyphens, 3-64 chars.",
        )
    if not validate_domain(domain):
        return False, "Invalid domain format"

    templates_dir = _get_templates_dir()
    template_path = templates_dir / app_type / "docker-compose.yml"
    if not template_path.exists():
        return False, f"Template {app_type} not found"

    apps_dir = _get_apps_dir()
    app_dir = apps_dir / name
    if app_dir.exists():
        return False, f"App {name} already exists"

    safe_env = sanitize_env_vars(env_vars) or {}

    with open(template_path) as f:
        compose = f.read()

    compose = compose.replace("${APP_NAME}", name)
    compose = compose.replace("${DOMAIN}", domain)

    for key, value in safe_env.items():
        compose = compose.replace(f"${{{key}}}", value)

    app_dir.mkdir(parents=True, exist_ok=True)

    with open(app_dir / "docker-compose.yml", "w") as f:
        f.write(compose)

    for key, value in safe_env.items():
        with open(app_dir / ".env", "a") as f:
            f.write(f"{key}={value}\n")

    result = subprocess.run(
        [DOCKER_COMPOSE_CMD, "compose", "up", "-d"],
        cwd=app_dir,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error("Deploy failed for %s: %s", name, result.stderr)
        shutil.rmtree(app_dir, ignore_errors=True)
        return False, result.stderr

    logger.info("Deployed app %s (%s) at %s", name, app_type, domain)
    return True, None


def start(name):
    apps_dir = _get_apps_dir()
    app_dir = apps_dir / name
    if not app_dir.exists():
        return False, "App directory not found"

    result = subprocess.run(
        [DOCKER_COMPOSE_CMD, "compose", "start"],
        cwd=app_dir,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error("Start failed for %s: %s", name, result.stderr)
        return False, result.stderr

    logger.info("Started app %s", name)
    return True, None


def stop(name):
    apps_dir = _get_apps_dir()
    app_dir = apps_dir / name
    if not app_dir.exists():
        return False, "App directory not found"

    result = subprocess.run(
        [DOCKER_COMPOSE_CMD, "compose", "stop"],
        cwd=app_dir,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error("Stop failed for %s: %s", name, result.stderr)
        return False, result.stderr

    logger.info("Stopped app %s", name)
    return True, None


def remove(name):
    apps_dir = _get_apps_dir()
    app_dir = apps_dir / name
    if not app_dir.exists():
        return False, "App directory not found"

    result = subprocess.run(
        [DOCKER_COMPOSE_CMD, "compose", "down", "-v"],
        cwd=app_dir,
        capture_output=True,
        text=True,
    )

    shutil.rmtree(app_dir, ignore_errors=True)

    if result.returncode != 0:
        logger.warning("Remove had errors for %s: %s", name, result.stderr)
        return False, result.stderr

    logger.info("Removed app %s", name)
    return True, None


def get_logs(name, tail=100):
    apps_dir = _get_apps_dir()
    app_dir = apps_dir / name
    if not app_dir.exists():
        return None

    result = subprocess.run(
        [DOCKER_COMPOSE_CMD, "compose", "logs", "--tail", str(tail)],
        cwd=app_dir,
        capture_output=True,
        text=True,
    )

    return result.stdout if result.returncode == 0 else None


def list_templates():
    templates_dir = _get_templates_dir()
    apps = []
    if not templates_dir.exists():
        return apps
    for template_dir in sorted(templates_dir.iterdir()):
        if not template_dir.is_dir():
            continue
        manifest_path = template_dir / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                apps.append(json.load(f))
        else:
            apps.append(
                {
                    "name": template_dir.name.title(),
                    "id": template_dir.name,
                    "description": f"{template_dir.name} self-hosted app",
                    "category": "misc",
                }
            )
    return apps
