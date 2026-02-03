"""Base scanner class and utilities for AWS resource scanning"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    """Result from scanning a resource type"""
    resource_type: str
    sheet_name: str
    resources: List[Dict[str, Any]]
    errors: List[str]
    is_global: bool = False


def format_tags(tags: Optional[List[Dict[str, str]]]) -> str:
    """
    Format AWS tags into a single string.
    Input: [{"Key": "Name", "Value": "MyResource"}, {"Key": "Env", "Value": "prod"}]
    Output: "Name=MyResource; Env=prod"
    """
    if not tags:
        return ""
    
    tag_strings = []
    for tag in tags:
        key = tag.get('Key', '')
        value = tag.get('Value', '')
        if key:
            tag_strings.append(f"{key}={value}")
    
    return "; ".join(tag_strings)


def get_name_from_tags(tags: Optional[List[Dict[str, str]]]) -> str:
    """Extract the Name tag value from a list of tags"""
    if not tags:
        return "N/A"
    
    for tag in tags:
        if tag.get('Key') == 'Name':
            return tag.get('Value', 'N/A')
    
    return "N/A"


def safe_get(data: dict, *keys, default: Any = "N/A") -> Any:
    """Safely get nested dictionary values"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data if data is not None else default


class BaseScanner(ABC):
    """Abstract base class for all resource scanners"""
    
    # Override in subclasses
    resource_type: str = "Unknown"
    sheet_name: str = "Unknown"
    is_global: bool = False  # True for IAM, S3, CloudFront, etc.
    
    def __init__(self):
        self.resources: List[Dict[str, Any]] = []
        self.errors: List[str] = []
    
    @abstractmethod
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """
        Scan for resources in a specific account/region.
        Must be implemented by subclasses.
        
        Args:
            session: boto3 Session with credentials for the target account
            account_id: AWS account ID
            account_name: Human-readable account name
            region: AWS region to scan
            
        Returns:
            List of resource dictionaries with standardized fields
        """
        pass
    
    def get_columns(self) -> List[str]:
        """
        Return the column headers for this resource type.
        Override in subclasses for custom columns.
        """
        return [
            "Resource Name",
            "Resource ID", 
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Created Date",
            "State/Status",
            "Tags"
        ]
    
    def scan_account_region(
        self, 
        credentials: dict, 
        account_id: str, 
        account_name: str, 
        region: str
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Scan a specific account/region combination.
        Handles errors gracefully.
        """
        resources = []
        error = None
        
        try:
            # Create session with temporary credentials
            session = boto3.Session(
                aws_access_key_id=credentials['aws_access_key_id'],
                aws_secret_access_key=credentials['aws_secret_access_key'],
                aws_session_token=credentials['aws_session_token'],
                region_name=region
            )
            
            resources = self.scan(session, account_id, account_name, region)
            logger.debug(f"{self.resource_type}: Found {len(resources)} in {account_id}/{region}")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code in ['AccessDenied', 'UnauthorizedAccess']:
                error = f"{self.resource_type} - {account_id} ({account_name}) - {region}: Access Denied"
            else:
                error = f"{self.resource_type} - {account_id} ({account_name}) - {region}: {str(e)}"
            logger.warning(error)
            
        except Exception as e:
            error = f"{self.resource_type} - {account_id} ({account_name}) - {region}: {str(e)}"
            logger.error(error)
        
        return resources, error
    
    def get_result(self) -> ScanResult:
        """Get the scan result for this scanner"""
        return ScanResult(
            resource_type=self.resource_type,
            sheet_name=self.sheet_name,
            resources=self.resources,
            errors=self.errors,
            is_global=self.is_global
        )
    
    def reset(self):
        """Reset scanner state for a new scan"""
        self.resources = []
        self.errors = []


class GlobalResourceScanner(BaseScanner):
    """Base class for global resources (IAM, S3, CloudFront, etc.)"""
    
    is_global: bool = True
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """
        For global resources, region parameter is ignored.
        The region field in results will be set to 'global'.
        """
        pass
