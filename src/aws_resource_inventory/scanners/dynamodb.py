"""DynamoDB Table Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags


class DynamoDBScanner(BaseScanner):
    """Scanner for DynamoDB Tables"""
    
    resource_type = "DynamoDB Table"
    sheet_name = "DynamoDB Tables"
    
    def get_columns(self) -> List[str]:
        return [
            "Table Name",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Status",
            "Billing Mode",
            "Item Count",
            "Table Size (Bytes)",
            "Read Capacity",
            "Write Capacity",
            "Global Secondary Indexes",
            "Encryption",
            "Created Time",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan DynamoDB tables in the specified account/region"""
        resources = []
        dynamodb = session.client('dynamodb', region_name=region)
        
        # List tables
        paginator = dynamodb.get_paginator('list_tables')
        table_names = []
        for page in paginator.paginate():
            table_names.extend(page.get('TableNames', []))
        
        # Describe each table
        for table_name in table_names:
            try:
                response = dynamodb.describe_table(TableName=table_name)
                table = response.get('Table', {})
                
                arn = table.get('TableArn', f"arn:aws:dynamodb:{region}:{account_id}:table/{table_name}")
                
                # Get tags
                tags = []
                try:
                    tag_response = dynamodb.list_tags_of_resource(ResourceArn=arn)
                    tags = tag_response.get('Tags', [])
                except Exception:
                    pass
                
                # Get billing mode
                billing_mode = table.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')
                
                # Get provisioned throughput
                throughput = table.get('ProvisionedThroughput', {})
                read_capacity = throughput.get('ReadCapacityUnits', 'N/A') if billing_mode == 'PROVISIONED' else 'On-Demand'
                write_capacity = throughput.get('WriteCapacityUnits', 'N/A') if billing_mode == 'PROVISIONED' else 'On-Demand'
                
                # Get GSI count
                gsi_count = len(table.get('GlobalSecondaryIndexes', []))
                
                # Get encryption
                sse = table.get('SSEDescription', {})
                encryption = sse.get('SSEType', 'DEFAULT') if sse.get('Status') == 'ENABLED' else 'None'
                
                resources.append({
                    "Table Name": table_name,
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "ARN": arn,
                    "Status": table.get('TableStatus', 'N/A'),
                    "Billing Mode": billing_mode,
                    "Item Count": table.get('ItemCount', 0),
                    "Table Size (Bytes)": table.get('TableSizeBytes', 0),
                    "Read Capacity": read_capacity,
                    "Write Capacity": write_capacity,
                    "Global Secondary Indexes": gsi_count,
                    "Encryption": encryption,
                    "Created Time": str(table.get('CreationDateTime', 'N/A')),
                    "Tags": format_tags(tags)
                })
            except Exception:
                continue
        
        return resources
