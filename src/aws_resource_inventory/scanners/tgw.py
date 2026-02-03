"""Transit Gateway Attachment Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags, get_name_from_tags


class TransitGatewayAttachmentScanner(BaseScanner):
    """Scanner for Transit Gateway Attachments"""
    
    resource_type = "TGW Attachment"
    sheet_name = "TGW Attachments"
    
    def get_columns(self) -> List[str]:
        return [
            "Attachment Name",
            "Attachment ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Transit Gateway ID",
            "Resource Type",
            "Resource ID",
            "State",
            "Association State",
            "Created Time",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan Transit Gateway Attachments in the specified account/region"""
        resources = []
        ec2 = session.client('ec2', region_name=region)
        
        try:
            paginator = ec2.get_paginator('describe_transit_gateway_attachments')
            for page in paginator.paginate():
                for attachment in page.get('TransitGatewayAttachments', []):
                    attachment_id = attachment['TransitGatewayAttachmentId']
                    tags = attachment.get('Tags', [])
                    arn = f"arn:aws:ec2:{region}:{account_id}:transit-gateway-attachment/{attachment_id}"
                    
                    # Get association state
                    association = attachment.get('Association', {})
                    association_state = association.get('State', 'N/A')
                    
                    resources.append({
                        "Attachment Name": get_name_from_tags(tags),
                        "Attachment ID": attachment_id,
                        "Account ID": account_id,
                        "Account Name": account_name,
                        "Region": region,
                        "ARN": arn,
                        "Transit Gateway ID": attachment.get('TransitGatewayId', 'N/A'),
                        "Resource Type": attachment.get('ResourceType', 'N/A'),
                        "Resource ID": attachment.get('ResourceId', 'N/A'),
                        "State": attachment.get('State', 'N/A'),
                        "Association State": association_state,
                        "Created Time": str(attachment.get('CreationTime', 'N/A')),
                        "Tags": format_tags(tags)
                    })
        except Exception:
            # TGW might not be available or accessible
            pass
        
        return resources
