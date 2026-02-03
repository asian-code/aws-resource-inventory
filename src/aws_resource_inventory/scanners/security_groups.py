"""Security Group Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags, get_name_from_tags


class SecurityGroupScanner(BaseScanner):
    """Scanner for Security Groups"""
    
    resource_type = "Security Group"
    sheet_name = "Security Groups"
    
    def get_columns(self) -> List[str]:
        return [
            "Security Group Name",
            "Security Group ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "VPC ID",
            "Description",
            "Inbound Rules Count",
            "Outbound Rules Count",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan Security Groups in the specified account/region"""
        resources = []
        ec2 = session.client('ec2', region_name=region)
        
        paginator = ec2.get_paginator('describe_security_groups')
        for page in paginator.paginate():
            for sg in page.get('SecurityGroups', []):
                sg_id = sg['GroupId']
                tags = sg.get('Tags', [])
                arn = f"arn:aws:ec2:{region}:{account_id}:security-group/{sg_id}"
                
                resources.append({
                    "Security Group Name": sg.get('GroupName', 'N/A'),
                    "Security Group ID": sg_id,
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "ARN": arn,
                    "VPC ID": sg.get('VpcId', 'N/A'),
                    "Description": sg.get('Description', 'N/A'),
                    "Inbound Rules Count": len(sg.get('IpPermissions', [])),
                    "Outbound Rules Count": len(sg.get('IpPermissionsEgress', [])),
                    "Tags": format_tags(tags)
                })
        
        return resources
