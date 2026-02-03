"""KMS Key Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags


class KMSScanner(BaseScanner):
    """Scanner for KMS Keys"""
    
    resource_type = "KMS Key"
    sheet_name = "KMS Keys"
    
    def get_columns(self) -> List[str]:
        return [
            "Key Alias",
            "Key ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Key State",
            "Key Spec",
            "Key Usage",
            "Origin",
            "Key Manager",
            "Rotation Enabled",
            "Created Date",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan KMS keys in the specified account/region"""
        resources = []
        kms = session.client('kms', region_name=region)
        
        # Get all aliases for lookup
        aliases = {}
        try:
            alias_paginator = kms.get_paginator('list_aliases')
            for page in alias_paginator.paginate():
                for alias in page.get('Aliases', []):
                    if alias.get('TargetKeyId'):
                        aliases[alias['TargetKeyId']] = alias.get('AliasName', 'N/A')
        except Exception:
            pass
        
        # List all keys
        paginator = kms.get_paginator('list_keys')
        for page in paginator.paginate():
            for key in page.get('Keys', []):
                key_id = key['KeyId']
                key_arn = key['KeyArn']
                
                # Get key details
                try:
                    key_response = kms.describe_key(KeyId=key_id)
                    key_metadata = key_response.get('KeyMetadata', {})
                    
                    # Skip AWS managed keys unless they have a custom alias
                    if key_metadata.get('KeyManager') == 'AWS' and key_id not in aliases:
                        continue
                    
                    # Get rotation status
                    rotation_enabled = 'N/A'
                    try:
                        if key_metadata.get('KeyManager') == 'CUSTOMER':
                            rotation_response = kms.get_key_rotation_status(KeyId=key_id)
                            rotation_enabled = 'Yes' if rotation_response.get('KeyRotationEnabled') else 'No'
                    except Exception:
                        pass
                    
                    # Get tags
                    tags = []
                    try:
                        tag_response = kms.list_resource_tags(KeyId=key_id)
                        tags = tag_response.get('Tags', [])
                    except Exception:
                        pass
                    
                    resources.append({
                        "Key Alias": aliases.get(key_id, 'N/A'),
                        "Key ID": key_id,
                        "Account ID": account_id,
                        "Account Name": account_name,
                        "Region": region,
                        "ARN": key_arn,
                        "Key State": key_metadata.get('KeyState', 'N/A'),
                        "Key Spec": key_metadata.get('KeySpec', 'N/A'),
                        "Key Usage": key_metadata.get('KeyUsage', 'N/A'),
                        "Origin": key_metadata.get('Origin', 'N/A'),
                        "Key Manager": key_metadata.get('KeyManager', 'N/A'),
                        "Rotation Enabled": rotation_enabled,
                        "Created Date": str(key_metadata.get('CreationDate', 'N/A')),
                        "Tags": format_tags(tags)
                    })
                except Exception:
                    continue
        
        return resources
