"""Unit tests for configuration module."""

import json
import pytest
from pathlib import Path
from aws_resource_inventory.config import Config, load_config


class TestConfig:
    """Test the Config dataclass."""

    def test_config_initialization(self, sample_config):
        """Test basic config initialization."""
        config = Config(
            sso_start_url=sample_config["sso_start_url"],
            sso_region=sample_config["sso_region"],
            role_name=sample_config["role_name"]
        )
        
        assert config.sso_start_url == sample_config["sso_start_url"]
        assert config.sso_region == sample_config["sso_region"]
        assert config.role_name == sample_config["role_name"]
        assert config.max_workers == 20  # Default value
        assert len(config.target_regions) == 2  # Default regions

    def test_config_with_custom_values(self, sample_config):
        """Test config with custom values."""
        config = Config(
            sso_start_url=sample_config["sso_start_url"],
            sso_region=sample_config["sso_region"],
            role_name=sample_config["role_name"],
            target_regions=["us-east-1"],
            max_workers=10,
            account_blacklist={"111111111111", "222222222222"}
        )
        
        assert config.max_workers == 10
        assert len(config.target_regions) == 1
        assert len(config.account_blacklist) == 2

    def test_is_account_allowed(self, sample_config):
        """Test account blacklist filtering."""
        config = Config(
            sso_start_url=sample_config["sso_start_url"],
            sso_region=sample_config["sso_region"],
            role_name=sample_config["role_name"],
            account_blacklist={"123456789012"}
        )
        
        assert not config.is_account_allowed("123456789012")
        assert config.is_account_allowed("999999999999")

    def test_filter_accounts(self, sample_config):
        """Test filtering accounts based on blacklist."""
        config = Config(
            sso_start_url=sample_config["sso_start_url"],
            sso_region=sample_config["sso_region"],
            role_name=sample_config["role_name"],
            account_blacklist={"111111111111"}
        )
        
        accounts = {
            "111111111111": "Blocked Account",
            "222222222222": "Allowed Account",
            "333333333333": "Another Allowed Account"
        }
        
        filtered = config.filter_accounts(accounts)
        assert len(filtered) == 2
        assert "111111111111" not in filtered
        assert "222222222222" in filtered


class TestLoadConfig:
    """Test the load_config function."""

    def test_load_config_success(self, tmp_path, sample_config):
        """Test successful config loading from file."""
        config_file = tmp_path / "test-config.json"
        config_file.write_text(json.dumps(sample_config))
        
        config = load_config(str(config_file))
        
        assert config.sso_start_url == sample_config["sso_start_url"]
        assert config.sso_region == sample_config["sso_region"]
        assert config.role_name == sample_config["role_name"]

    def test_load_config_missing_file(self):
        """Test error handling for missing config file."""
        with pytest.raises(SystemExit):
            load_config("nonexistent.json")

    def test_load_config_invalid_json(self, tmp_path):
        """Test error handling for invalid JSON."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("{invalid json")
        
        with pytest.raises(SystemExit):
            load_config(str(config_file))

    def test_load_config_missing_required_key(self, tmp_path):
        """Test error handling for missing required keys."""
        config_file = tmp_path / "incomplete.json"
        config_file.write_text(json.dumps({"sso_region": "us-east-1"}))
        
        with pytest.raises(SystemExit):
            load_config(str(config_file))
