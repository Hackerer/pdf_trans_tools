"""Tests for config module"""
import os
import tempfile
import pytest
from pdf_trans_tools.config import Config, load_config, DEFAULT_CONFIG_PATHS


class TestConfig:
    """Test cases for Config class."""

    def test_config_init_empty(self):
        """Test Config initialization without file."""
        config = Config()
        assert config._config == {}
        assert config._loaded_from is None

    def test_config_get_default(self):
        """Test Config.get with default value."""
        config = Config()
        result = config.get("nonexistent", "default")
        assert result == "default"

    def test_config_get_nested(self):
        """Test Config.get with nested keys."""
        config = Config()
        config._config = {"api": {"google_key": "test-key"}}
        result = config.get("api.google_key")
        assert result == "test-key"

    def test_config_get_api_key(self):
        """Test Config.get_api_key."""
        config = Config()
        config._config = {"api": {"google_key": "config-key"}}
        result = config.get_api_key("google")
        assert result == "config-key"

    def test_config_get_api_key_env_override(self):
        """Test Config.get_api_key with environment variable override."""
        config = Config()
        config._config = {"api": {"google_key": "config-key"}}
        os.environ["GOOGLE_API_KEY"] = "env-key"
        try:
            result = config.get_api_key("google")
            assert result == "env-key"
        finally:
            del os.environ["GOOGLE_API_KEY"]

    def test_config_get_target_lang(self):
        """Test Config.get_target_lang."""
        config = Config()
        config._config = {"target_lang": "fr"}
        result = config.get_target_lang()
        assert result == "fr"

    def test_config_get_target_lang_default(self):
        """Test Config.get_target_lang default."""
        config = Config()
        result = config.get_target_lang()
        assert result == "en"

    def test_config_get_cache_settings(self):
        """Test Config.get_cache_settings."""
        config = Config()
        config._config = {"cache": {"enabled": False, "max_size": 500}}
        settings = config.get_cache_settings()
        assert settings["enabled"] is False
        assert settings["max_size"] == 500
        assert settings["ttl"] == 3600  # default

    def test_load_config(self):
        """Test load_config function."""
        result = load_config()
        assert isinstance(result, Config)

    def test_config_loaded_from(self):
        """Test Config.loaded_from property."""
        config = Config()
        assert config.loaded_from is None
