import os
import tempfile

import yaml

from backend.core.config import load_config, get_config, get_database_uri, _deep_merge


class TestConfig:
    def test_defaults_loaded(self):
        import backend.core.config as cfg

        cfg._config = None
        config = get_config()
        assert config["base_domain"] == "selfhostbox.local"
        assert config["ssl"]["enabled"] is True
        assert config["database"]["type"] == "sqlite"

    def test_deep_merge(self):
        base = {"a": 1, "b": {"c": 2, "d": 3}, "e": 5}
        override = {"b": {"c": 99}, "f": 6}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": {"c": 99, "d": 3}, "e": 5, "f": 6}

    def test_database_uri_sqlite(self):
        import backend.core.config as cfg

        cfg._config = {"database": {"type": "sqlite", "path": "/tmp/test.db"}}
        uri = get_database_uri()
        assert uri == "sqlite:////tmp/test.db"

    def test_database_uri_postgresql(self):
        import backend.core.config as cfg

        cfg._config = {
            "database": {"type": "postgresql", "uri": "postgresql://localhost/test"}
        }
        uri = get_database_uri()
        assert uri == "postgresql://localhost/test"

    def test_config_from_file(self):
        import backend.core.config as cfg

        cfg._config = None
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            yaml.dump({"base_domain": "test.local", "ssl": {"enabled": False}}, f)
            f.flush()
            os.environ["SELFHOSTBOX_CONFIG"] = f.name
            try:
                cfg._config = None
                config = load_config()
                assert config["base_domain"] == "test.local"
                assert config["ssl"]["enabled"] is False
            finally:
                del os.environ["SELFHOSTBOX_CONFIG"]
                os.unlink(f.name)
                cfg._config = None
