"""Lambda Function Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags


class LambdaScanner(BaseScanner):
    """Scanner for Lambda functions"""
    
    resource_type = "Lambda Function"
    sheet_name = "Lambda Functions"
    
    def get_columns(self) -> List[str]:
        return [
            "Function Name",
            "Function ARN",
            "Account ID",
            "Account Name",
            "Region",
            "Runtime",
            "Handler",
            "Memory (MB)",
            "Timeout (sec)",
            "Code Size (bytes)",
            "Last Modified",
            "State",
            "Role ARN",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan Lambda functions in the specified account/region"""
        resources = []
        lambda_client = session.client('lambda', region_name=region)
        
        paginator = lambda_client.get_paginator('list_functions')
        for page in paginator.paginate():
            for func in page.get('Functions', []):
                func_name = func['FunctionName']
                func_arn = func['FunctionArn']
                
                # Get tags for the function
                tags = []
                try:
                    tag_response = lambda_client.list_tags(Resource=func_arn)
                    tags_dict = tag_response.get('Tags', {})
                    tags = [{"Key": k, "Value": v} for k, v in tags_dict.items()]
                except Exception:
                    pass  # Tags not accessible or don't exist
                
                resources.append({
                    "Function Name": func_name,
                    "Function ARN": func_arn,
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "Runtime": func.get('Runtime', 'N/A'),
                    "Handler": func.get('Handler', 'N/A'),
                    "Memory (MB)": func.get('MemorySize', 'N/A'),
                    "Timeout (sec)": func.get('Timeout', 'N/A'),
                    "Code Size (bytes)": func.get('CodeSize', 'N/A'),
                    "Last Modified": func.get('LastModified', 'N/A'),
                    "State": func.get('State', 'Active'),
                    "Role ARN": func.get('Role', 'N/A'),
                    "Tags": format_tags(tags)
                })
        
        return resources
