"""API Gateway Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags


class APIGatewayScanner(BaseScanner):
    """Scanner for API Gateway REST APIs and HTTP APIs"""
    
    resource_type = "API Gateway"
    sheet_name = "API Gateway"
    
    def get_columns(self) -> List[str]:
        return [
            "API Name",
            "API ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "API Type",
            "Protocol Type",
            "Endpoint Type",
            "Description",
            "Created Date",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan API Gateway APIs in the specified account/region"""
        resources = []
        
        # Scan REST APIs (API Gateway v1)
        try:
            apigateway = session.client('apigateway', region_name=region)
            
            paginator = apigateway.get_paginator('get_rest_apis')
            for page in paginator.paginate():
                for api in page.get('items', []):
                    api_id = api['id']
                    api_name = api.get('name', 'N/A')
                    arn = f"arn:aws:apigateway:{region}::/restapis/{api_id}"
                    
                    # Get endpoint configuration
                    endpoint_config = api.get('endpointConfiguration', {})
                    endpoint_types = endpoint_config.get('types', ['EDGE'])
                    
                    # Get tags
                    tags_dict = api.get('tags', {})
                    tags = [{"Key": k, "Value": v} for k, v in tags_dict.items()]
                    
                    resources.append({
                        "API Name": api_name,
                        "API ID": api_id,
                        "Account ID": account_id,
                        "Account Name": account_name,
                        "Region": region,
                        "ARN": arn,
                        "API Type": "REST API",
                        "Protocol Type": "REST",
                        "Endpoint Type": ", ".join(endpoint_types),
                        "Description": api.get('description', 'N/A'),
                        "Created Date": str(api.get('createdDate', 'N/A')),
                        "Tags": format_tags(tags)
                    })
        except Exception:
            pass
        
        # Scan HTTP APIs (API Gateway v2)
        try:
            apigatewayv2 = session.client('apigatewayv2', region_name=region)
            
            # No paginator for get_apis in v2, use manual pagination
            next_token = None
            while True:
                params = {}
                if next_token:
                    params['NextToken'] = next_token
                
                response = apigatewayv2.get_apis(**params)
                
                for api in response.get('Items', []):
                    api_id = api['ApiId']
                    api_name = api.get('Name', 'N/A')
                    arn = f"arn:aws:apigateway:{region}::/apis/{api_id}"
                    
                    # Get tags
                    tags_dict = api.get('Tags', {})
                    tags = [{"Key": k, "Value": v} for k, v in tags_dict.items()]
                    
                    resources.append({
                        "API Name": api_name,
                        "API ID": api_id,
                        "Account ID": account_id,
                        "Account Name": account_name,
                        "Region": region,
                        "ARN": arn,
                        "API Type": "HTTP API",
                        "Protocol Type": api.get('ProtocolType', 'HTTP'),
                        "Endpoint Type": api.get('ApiEndpoint', 'N/A'),
                        "Description": api.get('Description', 'N/A'),
                        "Created Date": str(api.get('CreatedDate', 'N/A')),
                        "Tags": format_tags(tags)
                    })
                
                next_token = response.get('NextToken')
                if not next_token:
                    break
        except Exception:
            pass
        
        return resources
