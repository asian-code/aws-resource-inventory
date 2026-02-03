"""EKS Cluster Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags


class EKSScanner(BaseScanner):
    """Scanner for EKS Clusters"""
    
    resource_type = "EKS Cluster"
    sheet_name = "EKS Clusters"
    
    def get_columns(self) -> List[str]:
        return [
            "Cluster Name",
            "Cluster ARN",
            "Account ID",
            "Account Name",
            "Region",
            "Status",
            "Kubernetes Version",
            "Platform Version",
            "Endpoint",
            "Role ARN",
            "VPC ID",
            "Created At",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan EKS clusters in the specified account/region"""
        resources = []
        eks = session.client('eks', region_name=region)
        
        # List clusters
        paginator = eks.get_paginator('list_clusters')
        cluster_names = []
        for page in paginator.paginate():
            cluster_names.extend(page.get('clusters', []))
        
        # Describe each cluster
        for cluster_name in cluster_names:
            try:
                response = eks.describe_cluster(name=cluster_name)
                cluster = response.get('cluster', {})
                
                tags = cluster.get('tags', {})
                formatted_tags = [{"Key": k, "Value": v} for k, v in tags.items()]
                
                vpc_config = cluster.get('resourcesVpcConfig', {})
                
                resources.append({
                    "Cluster Name": cluster_name,
                    "Cluster ARN": cluster.get('arn', 'N/A'),
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "Status": cluster.get('status', 'N/A'),
                    "Kubernetes Version": cluster.get('version', 'N/A'),
                    "Platform Version": cluster.get('platformVersion', 'N/A'),
                    "Endpoint": cluster.get('endpoint', 'N/A'),
                    "Role ARN": cluster.get('roleArn', 'N/A'),
                    "VPC ID": vpc_config.get('vpcId', 'N/A'),
                    "Created At": str(cluster.get('createdAt', 'N/A')),
                    "Tags": format_tags(formatted_tags)
                })
            except Exception:
                continue
        
        return resources
