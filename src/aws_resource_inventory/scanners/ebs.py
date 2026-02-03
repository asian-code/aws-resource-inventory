"""EBS Volume Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags, get_name_from_tags


class EBSScanner(BaseScanner):
    """Scanner for EBS Volumes"""
    
    resource_type = "EBS Volume"
    sheet_name = "EBS Volumes"
    
    def get_columns(self) -> List[str]:
        return [
            "Volume Name",
            "Volume ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "State",
            "Volume Type",
            "Size (GiB)",
            "IOPS",
            "Throughput",
            "Encrypted",
            "Attached Instance",
            "Availability Zone",
            "Created Time",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan EBS volumes in the specified account/region"""
        resources = []
        ec2 = session.client('ec2', region_name=region)
        
        paginator = ec2.get_paginator('describe_volumes')
        for page in paginator.paginate():
            for volume in page.get('Volumes', []):
                volume_id = volume['VolumeId']
                tags = volume.get('Tags', [])
                arn = f"arn:aws:ec2:{region}:{account_id}:volume/{volume_id}"
                
                # Get attached instance
                attached_instance = 'Not Attached'
                attachments = volume.get('Attachments', [])
                if attachments:
                    attached_instances = [a.get('InstanceId', 'N/A') for a in attachments]
                    attached_instance = ", ".join(attached_instances)
                
                resources.append({
                    "Volume Name": get_name_from_tags(tags),
                    "Volume ID": volume_id,
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "ARN": arn,
                    "State": volume.get('State', 'N/A'),
                    "Volume Type": volume.get('VolumeType', 'N/A'),
                    "Size (GiB)": volume.get('Size', 'N/A'),
                    "IOPS": volume.get('Iops', 'N/A'),
                    "Throughput": volume.get('Throughput', 'N/A'),
                    "Encrypted": 'Yes' if volume.get('Encrypted') else 'No',
                    "Attached Instance": attached_instance,
                    "Availability Zone": volume.get('AvailabilityZone', 'N/A'),
                    "Created Time": str(volume.get('CreateTime', 'N/A')),
                    "Tags": format_tags(tags)
                })
        
        return resources
