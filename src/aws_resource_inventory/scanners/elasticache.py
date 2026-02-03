"""ElastiCache Cluster Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags


class ElastiCacheScanner(BaseScanner):
    """Scanner for ElastiCache Clusters"""
    
    resource_type = "ElastiCache Cluster"
    sheet_name = "ElastiCache Clusters"
    
    def get_columns(self) -> List[str]:
        return [
            "Cluster Name",
            "Cluster ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Status",
            "Engine",
            "Engine Version",
            "Node Type",
            "Num Nodes",
            "Replication Group ID",
            "Endpoint",
            "Port",
            "Encrypted",
            "Created Time",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan ElastiCache clusters in the specified account/region"""
        resources = []
        elasticache = session.client('elasticache', region_name=region)
        
        paginator = elasticache.get_paginator('describe_cache_clusters')
        for page in paginator.paginate(ShowCacheNodeInfo=True):
            for cluster in page.get('CacheClusters', []):
                cluster_id = cluster['CacheClusterId']
                arn = cluster.get('ARN', f"arn:aws:elasticache:{region}:{account_id}:cluster:{cluster_id}")
                
                # Get endpoint
                endpoint = 'N/A'
                port = 'N/A'
                config_endpoint = cluster.get('ConfigurationEndpoint', {})
                if config_endpoint:
                    endpoint = config_endpoint.get('Address', 'N/A')
                    port = config_endpoint.get('Port', 'N/A')
                elif cluster.get('CacheNodes'):
                    node = cluster['CacheNodes'][0]
                    ep = node.get('Endpoint', {})
                    endpoint = ep.get('Address', 'N/A')
                    port = ep.get('Port', 'N/A')
                
                # Get tags
                tags = []
                try:
                    tag_response = elasticache.list_tags_for_resource(ResourceName=arn)
                    tags = tag_response.get('TagList', [])
                except Exception:
                    pass
                
                resources.append({
                    "Cluster Name": cluster_id,
                    "Cluster ID": cluster_id,
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "ARN": arn,
                    "Status": cluster.get('CacheClusterStatus', 'N/A'),
                    "Engine": cluster.get('Engine', 'N/A'),
                    "Engine Version": cluster.get('EngineVersion', 'N/A'),
                    "Node Type": cluster.get('CacheNodeType', 'N/A'),
                    "Num Nodes": cluster.get('NumCacheNodes', 0),
                    "Replication Group ID": cluster.get('ReplicationGroupId', 'N/A'),
                    "Endpoint": endpoint,
                    "Port": port,
                    "Encrypted": 'Yes' if cluster.get('AtRestEncryptionEnabled') else 'No',
                    "Created Time": str(cluster.get('CacheClusterCreateTime', 'N/A')),
                    "Tags": format_tags(tags)
                })
        
        return resources
