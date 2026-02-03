"""EFS File System Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags, get_name_from_tags


class EFSScanner(BaseScanner):
    """Scanner for EFS File Systems"""
    
    resource_type = "EFS File System"
    sheet_name = "EFS File Systems"
    
    def get_columns(self) -> List[str]:
        return [
            "File System Name",
            "File System ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Lifecycle State",
            "Performance Mode",
            "Throughput Mode",
            "Size (Bytes)",
            "Encrypted",
            "Number of Mount Targets",
            "Creation Time",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan EFS file systems in the specified account/region"""
        resources = []
        efs = session.client('efs', region_name=region)
        
        paginator = efs.get_paginator('describe_file_systems')
        for page in paginator.paginate():
            for fs in page.get('FileSystems', []):
                fs_id = fs['FileSystemId']
                tags = fs.get('Tags', [])
                arn = fs.get('FileSystemArn', f"arn:aws:elasticfilesystem:{region}:{account_id}:file-system/{fs_id}")
                
                resources.append({
                    "File System Name": fs.get('Name', get_name_from_tags(tags)),
                    "File System ID": fs_id,
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "ARN": arn,
                    "Lifecycle State": fs.get('LifeCycleState', 'N/A'),
                    "Performance Mode": fs.get('PerformanceMode', 'N/A'),
                    "Throughput Mode": fs.get('ThroughputMode', 'N/A'),
                    "Size (Bytes)": fs.get('SizeInBytes', {}).get('Value', 'N/A'),
                    "Encrypted": 'Yes' if fs.get('Encrypted') else 'No',
                    "Number of Mount Targets": fs.get('NumberOfMountTargets', 0),
                    "Creation Time": str(fs.get('CreationTime', 'N/A')),
                    "Tags": format_tags(tags)
                })
        
        return resources
