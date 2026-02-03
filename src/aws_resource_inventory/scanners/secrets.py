"""Secrets Manager Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags


class SecretsManagerScanner(BaseScanner):
    """Scanner for Secrets Manager Secrets"""
    
    resource_type = "Secret"
    sheet_name = "Secrets Manager"
    
    def get_columns(self) -> List[str]:
        return [
            "Secret Name",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Description",
            "Rotation Enabled",
            "Rotation Lambda ARN",
            "Last Rotated Date",
            "Last Accessed Date",
            "Last Changed Date",
            "Created Date",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan Secrets Manager secrets in the specified account/region"""
        resources = []
        secretsmanager = session.client('secretsmanager', region_name=region)
        
        paginator = secretsmanager.get_paginator('list_secrets')
        for page in paginator.paginate():
            for secret in page.get('SecretList', []):
                tags = secret.get('Tags', [])
                
                resources.append({
                    "Secret Name": secret.get('Name', 'N/A'),
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "ARN": secret.get('ARN', 'N/A'),
                    "Description": secret.get('Description', 'N/A'),
                    "Rotation Enabled": 'Yes' if secret.get('RotationEnabled') else 'No',
                    "Rotation Lambda ARN": secret.get('RotationLambdaARN', 'N/A'),
                    "Last Rotated Date": str(secret.get('LastRotatedDate', 'Never')),
                    "Last Accessed Date": str(secret.get('LastAccessedDate', 'Never')),
                    "Last Changed Date": str(secret.get('LastChangedDate', 'N/A')),
                    "Created Date": str(secret.get('CreatedDate', 'N/A')),
                    "Tags": format_tags(tags)
                })
        
        return resources
