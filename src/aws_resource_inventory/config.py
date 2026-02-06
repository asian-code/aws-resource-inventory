"""Configuration management for AWS Resource Inventory Tool"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field


@dataclass
class Config:
    """Configuration settings for the inventory scanner"""
    
    # Cross-Account Role Settings
    cross_account_role_name: str = "AWSControlTowerExecution"
    
    # Scanning Settings
    target_regions: List[str] = field(default_factory=lambda: ['us-east-1', 'us-west-2'])
    max_workers: int = 20
    
    # Account Filtering
    account_blacklist: Set[str] = field(default_factory=set)
    
    # Output Settings
    output_dir: Path = field(default_factory=lambda: Path('output'))
    
    # S3 Upload Settings (for CI/CD pipeline)
    s3_bucket: Optional[str] = None
    s3_prefix: str = ""
    
    def __post_init__(self):
        """Validate and convert types after initialization"""
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Convert blacklist to set if it's a list
        if isinstance(self.account_blacklist, list):
            self.account_blacklist = set(self.account_blacklist)
    
    def is_account_allowed(self, account_id: str) -> bool:
        """Check if an account should be scanned (not in blacklist)"""
        return account_id not in self.account_blacklist
    
    def filter_accounts(self, accounts: Dict[str, str]) -> Dict[str, str]:
        """Filter accounts based on blacklist, returns {account_id: account_name}"""
        return {
            acc_id: acc_name 
            for acc_id, acc_name in accounts.items() 
            if self.is_account_allowed(acc_id)
        }


def load_config(config_path: str = 'inventory-config.json') -> Config:
    """Load configuration from JSON file or environment variables"""
    
    # First, try environment variables (for CI/CD)
    if os.environ.get('AWS_INVENTORY_CI'):
        return Config(
            cross_account_role_name=os.environ.get('CROSS_ACCOUNT_ROLE_NAME', 'AWSControlTowerExecution'),
            target_regions=os.environ.get('TARGET_REGIONS', 'us-east-1,us-west-2').split(','),
            max_workers=int(os.environ.get('MAX_WORKERS', '20')),
            account_blacklist=set(os.environ.get('ACCOUNT_BLACKLIST', '').split(',')) if os.environ.get('ACCOUNT_BLACKLIST') else set(),
            output_dir=Path(os.environ.get('OUTPUT_DIR', 'output')),
            s3_bucket=os.environ.get('S3_BUCKET'),
            s3_prefix=os.environ.get('S3_PREFIX', '')
        )
    
    # Otherwise, try loading from config file
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        return Config(
            cross_account_role_name=data.get('cross_account_role_name', 'AWSControlTowerExecution'),
            target_regions=data.get('target_regions', ['us-east-1', 'us-west-2']),
            max_workers=data.get('max_workers', 20),
            account_blacklist=set(data.get('account_blacklist', [])),
            output_dir=Path(data.get('output_dir', 'output')),
            s3_bucket=data.get('s3_bucket'),
            s3_prefix=data.get('s3_prefix', '')
        )
        
    except FileNotFoundError:
        # Return default config if no file found
        print(f"Info: Configuration file '{config_path}' not found, using defaults")
        return Config()
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)
