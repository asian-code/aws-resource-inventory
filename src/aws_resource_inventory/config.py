"""Configuration management for AWS Resource Inventory Tool"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field


@dataclass
class Config:
    """Configuration settings for the inventory scanner"""
    
    # SSO Settings
    sso_start_url: str
    sso_region: str
    role_name: str
    
    # Scanning Settings
    target_regions: List[str] = field(default_factory=lambda: ['us-east-1', 'us-west-2'])
    max_workers: int = 20
    
    # Account Filtering
    account_blacklist: Set[str] = field(default_factory=set)
    
    # Output Settings
    output_dir: Path = field(default_factory=lambda: Path('output'))
    
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


def load_config(config_path: str = 'sso-config.json') -> Config:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        return Config(
            sso_start_url=data['sso_start_url'],
            sso_region=data['sso_region'],
            role_name=data['role_name'],
            target_regions=data.get('target_regions', ['us-east-1', 'us-west-2']),
            max_workers=data.get('max_workers', 20),
            account_blacklist=set(data.get('account_blacklist', [])),
            output_dir=Path(data.get('output_dir', 'output'))
        )
        
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Missing required configuration key: {e}")
        sys.exit(1)
