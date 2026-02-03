"""AWS Resource Inventory Tool - Scan AWS resources across an organization."""

__version__ = "1.0.0"
__author__ = "Your Name"

from aws_resource_inventory.config import Config, load_config
from aws_resource_inventory.aws_auth import SSOAuthenticator
from aws_resource_inventory.main import AWSResourceInventory

__all__ = [
    "Config",
    "load_config",
    "SSOAuthenticator",
    "AWSResourceInventory",
    "__version__",
]
