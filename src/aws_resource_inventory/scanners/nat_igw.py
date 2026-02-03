"""NAT Gateway and Internet Gateway Scanners"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags, get_name_from_tags


class NATGatewayScanner(BaseScanner):
    """Scanner for NAT Gateways"""
    
    resource_type = "NAT Gateway"
    sheet_name = "NAT Gateways"
    
    def get_columns(self) -> List[str]:
        return [
            "NAT Gateway Name",
            "NAT Gateway ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "State",
            "VPC ID",
            "Subnet ID",
            "Connectivity Type",
            "Public IP",
            "Private IP",
            "Created Time",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan NAT Gateways in the specified account/region"""
        resources = []
        ec2 = session.client('ec2', region_name=region)
        
        paginator = ec2.get_paginator('describe_nat_gateways')
        for page in paginator.paginate():
            for nat in page.get('NatGateways', []):
                nat_id = nat['NatGatewayId']
                tags = nat.get('Tags', [])
                arn = f"arn:aws:ec2:{region}:{account_id}:natgateway/{nat_id}"
                
                # Get IP addresses
                public_ip = 'N/A'
                private_ip = 'N/A'
                addresses = nat.get('NatGatewayAddresses', [])
                if addresses:
                    public_ip = addresses[0].get('PublicIp', 'N/A')
                    private_ip = addresses[0].get('PrivateIp', 'N/A')
                
                resources.append({
                    "NAT Gateway Name": get_name_from_tags(tags),
                    "NAT Gateway ID": nat_id,
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "ARN": arn,
                    "State": nat.get('State', 'N/A'),
                    "VPC ID": nat.get('VpcId', 'N/A'),
                    "Subnet ID": nat.get('SubnetId', 'N/A'),
                    "Connectivity Type": nat.get('ConnectivityType', 'public'),
                    "Public IP": public_ip,
                    "Private IP": private_ip,
                    "Created Time": str(nat.get('CreateTime', 'N/A')),
                    "Tags": format_tags(tags)
                })
        
        return resources


class InternetGatewayScanner(BaseScanner):
    """Scanner for Internet Gateways"""
    
    resource_type = "Internet Gateway"
    sheet_name = "Internet Gateways"
    
    def get_columns(self) -> List[str]:
        return [
            "IGW Name",
            "IGW ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "State",
            "Attached VPC",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan Internet Gateways in the specified account/region"""
        resources = []
        ec2 = session.client('ec2', region_name=region)
        
        paginator = ec2.get_paginator('describe_internet_gateways')
        for page in paginator.paginate():
            for igw in page.get('InternetGateways', []):
                igw_id = igw['InternetGatewayId']
                tags = igw.get('Tags', [])
                arn = f"arn:aws:ec2:{region}:{account_id}:internet-gateway/{igw_id}"
                
                # Get attached VPC
                attached_vpc = 'Not Attached'
                state = 'detached'
                attachments = igw.get('Attachments', [])
                if attachments:
                    attached_vpc = attachments[0].get('VpcId', 'N/A')
                    state = attachments[0].get('State', 'attached')
                
                resources.append({
                    "IGW Name": get_name_from_tags(tags),
                    "IGW ID": igw_id,
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "ARN": arn,
                    "State": state,
                    "Attached VPC": attached_vpc,
                    "Tags": format_tags(tags)
                })
        
        return resources
