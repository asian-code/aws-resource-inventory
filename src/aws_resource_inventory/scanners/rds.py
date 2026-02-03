"""RDS Instance Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags


class RDSScanner(BaseScanner):
    """Scanner for RDS Instances"""
    
    resource_type = "RDS Instance"
    sheet_name = "RDS Instances"
    
    def get_columns(self) -> List[str]:
        return [
            "DB Instance Name",
            "DB Instance ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Status",
            "Engine",
            "Engine Version",
            "Instance Class",
            "Storage (GiB)",
            "Storage Type",
            "Multi-AZ",
            "Encrypted",
            "Endpoint",
            "Port",
            "VPC ID",
            "Created Time",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan RDS instances in the specified account/region"""
        resources = []
        rds = session.client('rds', region_name=region)
        
        paginator = rds.get_paginator('describe_db_instances')
        for page in paginator.paginate():
            for db in page.get('DBInstances', []):
                db_id = db['DBInstanceIdentifier']
                arn = db.get('DBInstanceArn', f"arn:aws:rds:{region}:{account_id}:db:{db_id}")
                
                # Get tags
                tags = []
                try:
                    tag_response = rds.list_tags_for_resource(ResourceName=arn)
                    tags = tag_response.get('TagList', [])
                except Exception:
                    pass
                
                endpoint = db.get('Endpoint', {})
                
                resources.append({
                    "DB Instance Name": db.get('DBName', 'N/A'),
                    "DB Instance ID": db_id,
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "ARN": arn,
                    "Status": db.get('DBInstanceStatus', 'N/A'),
                    "Engine": db.get('Engine', 'N/A'),
                    "Engine Version": db.get('EngineVersion', 'N/A'),
                    "Instance Class": db.get('DBInstanceClass', 'N/A'),
                    "Storage (GiB)": db.get('AllocatedStorage', 'N/A'),
                    "Storage Type": db.get('StorageType', 'N/A'),
                    "Multi-AZ": 'Yes' if db.get('MultiAZ') else 'No',
                    "Encrypted": 'Yes' if db.get('StorageEncrypted') else 'No',
                    "Endpoint": endpoint.get('Address', 'N/A'),
                    "Port": endpoint.get('Port', 'N/A'),
                    "VPC ID": db.get('DBSubnetGroup', {}).get('VpcId', 'N/A'),
                    "Created Time": str(db.get('InstanceCreateTime', 'N/A')),
                    "Tags": format_tags(tags)
                })
        
        return resources
