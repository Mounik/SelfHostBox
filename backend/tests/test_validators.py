import pytest

from backend.core.validators import (
    validate_app_name,
    validate_domain,
    validate_app_type,
    sanitize_env_vars,
)


class TestValidateAppName:
    @pytest.mark.parametrize(
        "name,expected",
        [
            ("my-app", True),
            ("nextcloud-abc1", True),
            ("a123", True),
            ("ab", False),
            ("UPPER", False),
            ("app with spaces", False),
            ("", False),
            ("-starts-dash", False),
            ("ends-dash-", False),
            ("a" * 65, False),
        ],
    )
    def test_app_name_validation(self, name, expected):
        assert validate_app_name(name) is expected

    def test_non_string(self):
        assert validate_app_name(123) is False
        assert validate_app_name(None) is False


class TestValidateDomain:
    @pytest.mark.parametrize(
        "domain,expected",
        [
            ("example.com", True),
            ("app.example.com", True),
            ("my-app.domain.org", True),
            ("a.b.c.d.e.com", True),
            ("invalid", False),
            ("", False),
            ("has space.com", False),
            (".starts-with-dot.com", False),
        ],
    )
    def test_domain_validation(self, domain, expected):
        assert validate_domain(domain) is expected

    def test_non_string(self):
        assert validate_domain(123) is False


class TestValidateAppType:
    @pytest.mark.parametrize(
        "app_type,expected",
        [
            ("nextcloud", True),
            ("uptime-kuma", True),
            ("UPPER", False),
            ("", False),
            ("has space", False),
        ],
    )
    def test_app_type_validation(self, app_type, expected):
        assert validate_app_type(app_type) is expected


class TestSanitizeEnvVars:
    def test_valid_env(self):
        assert sanitize_env_vars({"KEY": "val"}) == {"KEY": "val"}

    def test_invalid_key(self):
        assert sanitize_env_vars({"1BAD": "val"}) == {}

    def test_non_dict(self):
        assert sanitize_env_vars("not a dict") is None
        assert sanitize_env_vars(None) is None

    def test_int_value_converted(self):
        assert sanitize_env_vars({"GOOD_KEY": 123}) == {"GOOD_KEY": "123"}

    def test_underscore_key(self):
        assert sanitize_env_vars({"MY_KEY": "val"}) == {"MY_KEY": "val"}
