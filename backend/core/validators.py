import re

NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9\-]{1,62}[a-z0-9]$")
DOMAIN_PATTERN = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.){1,}[a-zA-Z]{2,}$"
)


def validate_app_name(name):
    if not isinstance(name, str):
        return False
    return bool(NAME_PATTERN.match(name))


def validate_domain(domain):
    if not isinstance(domain, str):
        return False
    return bool(DOMAIN_PATTERN.match(domain))


def validate_app_type(app_type):
    if not isinstance(app_type, str):
        return False
    return bool(re.match(r"^[a-z0-9\-]{1,50}$", app_type))


def sanitize_env_vars(env_vars):
    if not isinstance(env_vars, dict):
        return None
    sanitized = {}
    for key, value in env_vars.items():
        if not isinstance(key, str) or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            continue
        sanitized[key] = str(value)
    return sanitized
