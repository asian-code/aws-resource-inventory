"""CloudFront Distribution Scanner (Global Resource)"""

from typing import List, Dict, Any
import boto3
from .base import GlobalResourceScanner, format_tags


class CloudFrontScanner(GlobalResourceScanner):
    """Scanner for CloudFront Distributions (Global resource)"""
    
    resource_type = "CloudFront Distribution"
    sheet_name = "CloudFront"
    is_global = True
    
    def get_columns(self) -> List[str]:
        return [
            "Distribution ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Status",
            "Domain Name",
            "Aliases",
            "Origins",
            "Price Class",
            "HTTP Version",
            "IPv6 Enabled",
            "Enabled",
            "Last Modified",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan CloudFront distributions in the specified account (global)"""
        resources = []
        
        # CloudFront is global, so we use us-east-1
        cloudfront = session.client('cloudfront', region_name='us-east-1')
        
        try:
            paginator = cloudfront.get_paginator('list_distributions')
            for page in paginator.paginate():
                distribution_list = page.get('DistributionList', {})
                for dist in distribution_list.get('Items', []):
                    dist_id = dist['Id']
                    dist_arn = dist['ARN']
                    
                    # Get aliases
                    aliases_config = dist.get('Aliases', {})
                    aliases = aliases_config.get('Items', [])
                    
                    # Get origins
                    origins_config = dist.get('Origins', {})
                    origins = [o.get('DomainName', 'N/A') for o in origins_config.get('Items', [])]
                    
                    # Get tags
                    tags = []
                    try:
                        tag_response = cloudfront.list_tags_for_resource(Resource=dist_arn)
                        tags = tag_response.get('Tags', {}).get('Items', [])
                    except Exception:
                        pass
                    
                    resources.append({
                        "Distribution ID": dist_id,
                        "Account ID": account_id,
                        "Account Name": account_name,
                        "Region": "global",
                        "ARN": dist_arn,
                        "Status": dist.get('Status', 'N/A'),
                        "Domain Name": dist.get('DomainName', 'N/A'),
                        "Aliases": ", ".join(aliases) if aliases else 'None',
                        "Origins": ", ".join(origins) if origins else 'N/A',
                        "Price Class": dist.get('PriceClass', 'N/A'),
                        "HTTP Version": dist.get('HttpVersion', 'N/A'),
                        "IPv6 Enabled": 'Yes' if dist.get('IsIPV6Enabled') else 'No',
                        "Enabled": 'Yes' if dist.get('Enabled') else 'No',
                        "Last Modified": str(dist.get('LastModifiedTime', 'N/A')),
                        "Tags": format_tags(tags)
                    })
        except Exception:
            pass
        
        return resources
