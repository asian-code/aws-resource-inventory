"""Unit tests for scanner base classes."""

import pytest
from aws_resource_inventory.scanners.base import (
    BaseScanner,
    GlobalResourceScanner,
    ScanResult,
    format_tags,
    get_name_from_tags,
    safe_get
)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_format_tags_with_dict(self):
        """Test format_tags with dictionary input."""
        tags = {"Name": "test-resource", "Environment": "prod"}
        result = format_tags(tags)
        assert "Name=test-resource" in result
        assert "Environment=prod" in result

    def test_format_tags_with_list(self):
        """Test format_tags with list input."""
        tags = [
            {"Key": "Name", "Value": "test-resource"},
            {"Key": "Environment", "Value": "prod"}
        ]
        result = format_tags(tags)
        assert "Name=test-resource" in result
        assert "Environment=prod" in result

    def test_format_tags_empty(self):
        """Test format_tags with empty input."""
        assert format_tags({}) == ""
        assert format_tags([]) == ""
        assert format_tags(None) == ""

    def test_get_name_from_tags_dict(self):
        """Test get_name_from_tags with dictionary."""
        tags = {"Name": "my-resource", "Type": "test"}
        assert get_name_from_tags(tags) == "my-resource"

    def test_get_name_from_tags_list(self):
        """Test get_name_from_tags with list."""
        tags = [
            {"Key": "Name", "Value": "my-resource"},
            {"Key": "Type", "Value": "test"}
        ]
        assert get_name_from_tags(tags) == "my-resource"

    def test_get_name_from_tags_no_name(self):
        """Test get_name_from_tags when Name tag is missing."""
        tags = {"Type": "test"}
        assert get_name_from_tags(tags) == "-"

    def test_safe_get_with_value(self):
        """Test safe_get when value exists."""
        data = {"key": "value"}
        assert safe_get(data, "key") == "value"

    def test_safe_get_with_default(self):
        """Test safe_get with default value."""
        data = {"key": "value"}
        assert safe_get(data, "missing", "default") == "default"

    def test_safe_get_none(self):
        """Test safe_get with None data."""
        assert safe_get(None, "key") == "-"


class TestScanResult:
    """Test ScanResult dataclass."""

    def test_scan_result_creation(self):
        """Test creating a ScanResult."""
        result = ScanResult(
            scanner_name="EC2Scanner",
            resources=[{"id": "i-123", "name": "test"}],
            error=None
        )
        
        assert result.scanner_name == "EC2Scanner"
        assert len(result.resources) == 1
        assert result.error is None

    def test_scan_result_with_error(self):
        """Test ScanResult with error."""
        error_msg = "Access denied"
        result = ScanResult(
            scanner_name="EC2Scanner",
            resources=[],
            error=error_msg
        )
        
        assert result.error == error_msg
        assert len(result.resources) == 0


class TestBaseScanner:
    """Test BaseScanner abstract class."""

    def test_base_scanner_cannot_be_instantiated(self):
        """Test that BaseScanner cannot be instantiated directly."""
        # BaseScanner is abstract, attempting to instantiate should fail
        # unless all abstract methods are implemented
        with pytest.raises(TypeError):
            BaseScanner()


class TestGlobalResourceScanner:
    """Test GlobalResourceScanner abstract class."""

    def test_global_scanner_is_global(self):
        """Test that GlobalResourceScanner has is_global=True."""
        # Create a concrete implementation for testing
        class TestGlobalScanner(GlobalResourceScanner):
            sheet_name = "TestGlobal"
            
            def scan_account_region(self, credentials, account_id, account_name, region):
                return [], None
        
        scanner = TestGlobalScanner()
        assert scanner.is_global is True
