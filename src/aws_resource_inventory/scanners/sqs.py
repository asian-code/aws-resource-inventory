"""SQS Queue Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags


class SQSScanner(BaseScanner):
    """Scanner for SQS Queues"""
    
    resource_type = "SQS Queue"
    sheet_name = "SQS Queues"
    
    def get_columns(self) -> List[str]:
        return [
            "Queue Name",
            "Queue URL",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Queue Type",
            "Messages Available",
            "Messages In Flight",
            "Visibility Timeout (sec)",
            "Retention Period (sec)",
            "Max Message Size",
            "Delay Seconds",
            "Encrypted",
            "Created Timestamp",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan SQS queues in the specified account/region"""
        resources = []
        sqs = session.client('sqs', region_name=region)
        
        # List all queues
        paginator = sqs.get_paginator('list_queues')
        for page in paginator.paginate():
            for queue_url in page.get('QueueUrls', []):
                try:
                    # Get queue attributes
                    attr_response = sqs.get_queue_attributes(
                        QueueUrl=queue_url,
                        AttributeNames=['All']
                    )
                    attributes = attr_response.get('Attributes', {})
                    
                    queue_arn = attributes.get('QueueArn', 'N/A')
                    queue_name = queue_url.split('/')[-1]
                    
                    # Determine queue type
                    queue_type = 'FIFO' if queue_name.endswith('.fifo') else 'Standard'
                    
                    # Get tags
                    tags = []
                    try:
                        tag_response = sqs.list_queue_tags(QueueUrl=queue_url)
                        tags_dict = tag_response.get('Tags', {})
                        tags = [{"Key": k, "Value": v} for k, v in tags_dict.items()]
                    except Exception:
                        pass
                    
                    resources.append({
                        "Queue Name": queue_name,
                        "Queue URL": queue_url,
                        "Account ID": account_id,
                        "Account Name": account_name,
                        "Region": region,
                        "ARN": queue_arn,
                        "Queue Type": queue_type,
                        "Messages Available": attributes.get('ApproximateNumberOfMessages', 'N/A'),
                        "Messages In Flight": attributes.get('ApproximateNumberOfMessagesNotVisible', 'N/A'),
                        "Visibility Timeout (sec)": attributes.get('VisibilityTimeout', 'N/A'),
                        "Retention Period (sec)": attributes.get('MessageRetentionPeriod', 'N/A'),
                        "Max Message Size": attributes.get('MaximumMessageSize', 'N/A'),
                        "Delay Seconds": attributes.get('DelaySeconds', 'N/A'),
                        "Encrypted": 'Yes' if attributes.get('KmsMasterKeyId') else 'No',
                        "Created Timestamp": attributes.get('CreatedTimestamp', 'N/A'),
                        "Tags": format_tags(tags)
                    })
                except Exception:
                    continue
        
        return resources
