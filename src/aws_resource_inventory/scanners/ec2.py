"""EC2 Instance Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags, get_name_from_tags


class EC2Scanner(BaseScanner):
    """Scanner for EC2 instances"""
    
    resource_type = "EC2 Instance"
    sheet_name = "EC2 Instances"
    
    def get_columns(self) -> List[str]:
        return [
            "Instance Name",
            "Instance ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Instance State",
            "Instance Type",
            "Platform",
            "Private IP",
            "Public IP",
            "VPC ID",
            "Subnet ID",
            "IAM Instance Profile",
            "Launch Time",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan EC2 instances in the specified account/region"""
        resources = []
        ec2 = session.client('ec2', region_name=region)
        
        paginator = ec2.get_paginator('describe_instances')
        for page in paginator.paginate():
            for reservation in page.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    tags = instance.get('Tags', [])
                    
                    # Build ARN
                    instance_id = instance['InstanceId']
                    arn = f"arn:aws:ec2:{region}:{account_id}:instance/{instance_id}"
                    
                    # Get IAM instance profile
                    iam_profile = "N/A"
                    if instance.get('IamInstanceProfile'):
                        iam_profile = instance['IamInstanceProfile'].get('Arn', 'N/A')
                    
                    resources.append({
                        "Instance Name": get_name_from_tags(tags),
                        "Instance ID": instance_id,
                        "Account ID": account_id,
                        "Account Name": account_name,
                        "Region": region,
                        "ARN": arn,
                        "Instance State": instance.get('State', {}).get('Name', 'N/A'),
                        "Instance Type": instance.get('InstanceType', 'N/A'),
                        "Platform": instance.get('PlatformDetails', instance.get('Platform', 'Linux/UNIX')),
                        "Private IP": instance.get('PrivateIpAddress', 'N/A'),
                        "Public IP": instance.get('PublicIpAddress', 'N/A'),
                        "VPC ID": instance.get('VpcId', 'N/A'),
                        "Subnet ID": instance.get('SubnetId', 'N/A'),
                        "IAM Instance Profile": iam_profile,
                        "Launch Time": str(instance.get('LaunchTime', 'N/A')),
                        "Tags": format_tags(tags)
                    })
        
        return resources
