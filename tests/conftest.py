"""Test configuration and fixtures for AWS Resource Inventory tests."""

import pytest
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Sample configuration for testing."""
    return {
        "sso_start_url": "https://example.awsapps.com/start",
        "sso_region": "us-east-1",
        "role_name": "TestRole",
        "target_regions": ["us-east-1", "us-west-2"],
        "max_workers": 5,
        "account_blacklist": ["123456789012"],
        "output_dir": "output"
    }


@pytest.fixture
def sample_credentials() -> Dict[str, str]:
    """Sample AWS credentials for testing."""
    return {
        "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
        "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "SessionToken": "FwoGZXIvYXdzEBa...",
        "Expiration": "2026-02-02T23:59:59Z"
    }


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory for tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
