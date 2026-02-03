"""Redshift Cluster Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags


class RedshiftScanner(BaseScanner):
    """Scanner for Redshift Clusters"""
    
    resource_type = "Redshift Cluster"
    sheet_name = "Redshift Clusters"
    
    def get_columns(self) -> List[str]:
        return [
            "Cluster Name",
            "Cluster ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Status",
            "Node Type",
            "Number of Nodes",
            "Database Name",
            "Master Username",
            "Endpoint",
            "Port",
            "VPC ID",
            "Encrypted",
            "Created Time",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan Redshift clusters in the specified account/region"""
        resources = []
        redshift = session.client('redshift', region_name=region)
        
        paginator = redshift.get_paginator('describe_clusters')
        for page in paginator.paginate():
            for cluster in page.get('Clusters', []):
                cluster_id = cluster['ClusterIdentifier']
                
                # Build ARN
                arn = f"arn:aws:redshift:{region}:{account_id}:cluster:{cluster_id}"
                
                # Get tags
                tags = cluster.get('Tags', [])
                
                endpoint = cluster.get('Endpoint', {})
                
                resources.append({
                    "Cluster Name": cluster_id,
                    "Cluster ID": cluster_id,
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "ARN": arn,
                    "Status": cluster.get('ClusterStatus', 'N/A'),
                    "Node Type": cluster.get('NodeType', 'N/A'),
                    "Number of Nodes": cluster.get('NumberOfNodes', 0),
                    "Database Name": cluster.get('DBName', 'N/A'),
                    "Master Username": cluster.get('MasterUsername', 'N/A'),
                    "Endpoint": endpoint.get('Address', 'N/A'),
                    "Port": endpoint.get('Port', 'N/A'),
                    "VPC ID": cluster.get('VpcId', 'N/A'),
                    "Encrypted": 'Yes' if cluster.get('Encrypted') else 'No',
                    "Created Time": str(cluster.get('ClusterCreateTime', 'N/A')),
                    "Tags": format_tags(tags)
                })
        
        return resources
