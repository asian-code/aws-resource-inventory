"""SNS Topic Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags


class SNSScanner(BaseScanner):
    """Scanner for SNS Topics"""
    
    resource_type = "SNS Topic"
    sheet_name = "SNS Topics"
    
    def get_columns(self) -> List[str]:
        return [
            "Topic Name",
            "Topic ARN",
            "Account ID",
            "Account Name",
            "Region",
            "Display Name",
            "Subscriptions Confirmed",
            "Subscriptions Pending",
            "Subscriptions Deleted",
            "Delivery Policy",
            "KMS Key ID",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan SNS topics in the specified account/region"""
        resources = []
        sns = session.client('sns', region_name=region)
        
        paginator = sns.get_paginator('list_topics')
        for page in paginator.paginate():
            for topic in page.get('Topics', []):
                topic_arn = topic['TopicArn']
                topic_name = topic_arn.split(':')[-1]
                
                # Get topic attributes
                try:
                    attr_response = sns.get_topic_attributes(TopicArn=topic_arn)
                    attributes = attr_response.get('Attributes', {})
                    
                    # Get tags
                    tags = []
                    try:
                        tag_response = sns.list_tags_for_resource(ResourceArn=topic_arn)
                        tags = tag_response.get('Tags', [])
                    except Exception:
                        pass
                    
                    resources.append({
                        "Topic Name": topic_name,
                        "Topic ARN": topic_arn,
                        "Account ID": account_id,
                        "Account Name": account_name,
                        "Region": region,
                        "Display Name": attributes.get('DisplayName', 'N/A'),
                        "Subscriptions Confirmed": attributes.get('SubscriptionsConfirmed', 0),
                        "Subscriptions Pending": attributes.get('SubscriptionsPending', 0),
                        "Subscriptions Deleted": attributes.get('SubscriptionsDeleted', 0),
                        "Delivery Policy": 'Configured' if attributes.get('DeliveryPolicy') else 'Default',
                        "KMS Key ID": attributes.get('KmsMasterKeyId', 'None'),
                        "Tags": format_tags(tags)
                    })
                except Exception:
                    continue
        
        return resources
