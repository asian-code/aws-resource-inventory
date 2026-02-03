"""Elastic IP Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags, get_name_from_tags


class EIPScanner(BaseScanner):
    """Scanner for Elastic IPs"""
    
    resource_type = "Elastic IP"
    sheet_name = "Elastic IPs"
    
    def get_columns(self) -> List[str]:
        return [
            "EIP Name",
            "Allocation ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Public IP",
            "Private IP",
            "Domain",
            "Associated Instance",
            "Associated ENI",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan Elastic IPs in the specified account/region"""
        resources = []
        ec2 = session.client('ec2', region_name=region)
        
        response = ec2.describe_addresses()
        for eip in response.get('Addresses', []):
            allocation_id = eip.get('AllocationId', 'N/A')
            tags = eip.get('Tags', [])
            arn = f"arn:aws:ec2:{region}:{account_id}:elastic-ip/{allocation_id}" if allocation_id != 'N/A' else 'N/A'
            
            resources.append({
                "EIP Name": get_name_from_tags(tags),
                "Allocation ID": allocation_id,
                "Account ID": account_id,
                "Account Name": account_name,
                "Region": region,
                "ARN": arn,
                "Public IP": eip.get('PublicIp', 'N/A'),
                "Private IP": eip.get('PrivateIpAddress', 'N/A'),
                "Domain": eip.get('Domain', 'N/A'),
                "Associated Instance": eip.get('InstanceId', 'Not Associated'),
                "Associated ENI": eip.get('NetworkInterfaceId', 'N/A'),
                "Tags": format_tags(tags)
            })
        
        return resources
