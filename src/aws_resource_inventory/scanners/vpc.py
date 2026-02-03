"""VPC, Subnet, and Route Table Scanners"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags, get_name_from_tags


class VPCScanner(BaseScanner):
    """Scanner for VPCs"""
    
    resource_type = "VPC"
    sheet_name = "VPCs"
    
    def get_columns(self) -> List[str]:
        return [
            "VPC Name",
            "VPC ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "State",
            "CIDR Block",
            "Is Default",
            "DHCP Options ID",
            "Instance Tenancy",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan VPCs in the specified account/region"""
        resources = []
        ec2 = session.client('ec2', region_name=region)
        
        paginator = ec2.get_paginator('describe_vpcs')
        for page in paginator.paginate():
            for vpc in page.get('Vpcs', []):
                vpc_id = vpc['VpcId']
                tags = vpc.get('Tags', [])
                arn = f"arn:aws:ec2:{region}:{account_id}:vpc/{vpc_id}"
                
                # Get all CIDR blocks
                cidr_blocks = [vpc.get('CidrBlock', 'N/A')]
                for assoc in vpc.get('CidrBlockAssociationSet', []):
                    if assoc.get('CidrBlock') and assoc['CidrBlock'] not in cidr_blocks:
                        cidr_blocks.append(assoc['CidrBlock'])
                
                resources.append({
                    "VPC Name": get_name_from_tags(tags),
                    "VPC ID": vpc_id,
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "ARN": arn,
                    "State": vpc.get('State', 'N/A'),
                    "CIDR Block": ", ".join(cidr_blocks),
                    "Is Default": 'Yes' if vpc.get('IsDefault') else 'No',
                    "DHCP Options ID": vpc.get('DhcpOptionsId', 'N/A'),
                    "Instance Tenancy": vpc.get('InstanceTenancy', 'N/A'),
                    "Tags": format_tags(tags)
                })
        
        return resources


class SubnetScanner(BaseScanner):
    """Scanner for Subnets"""
    
    resource_type = "Subnet"
    sheet_name = "Subnets"
    
    def get_columns(self) -> List[str]:
        return [
            "Subnet Name",
            "Subnet ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "State",
            "VPC ID",
            "CIDR Block",
            "Availability Zone",
            "Available IPs",
            "Auto-assign Public IP",
            "Default for AZ",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan Subnets in the specified account/region"""
        resources = []
        ec2 = session.client('ec2', region_name=region)
        
        paginator = ec2.get_paginator('describe_subnets')
        for page in paginator.paginate():
            for subnet in page.get('Subnets', []):
                subnet_id = subnet['SubnetId']
                tags = subnet.get('Tags', [])
                arn = subnet.get('SubnetArn', f"arn:aws:ec2:{region}:{account_id}:subnet/{subnet_id}")
                
                resources.append({
                    "Subnet Name": get_name_from_tags(tags),
                    "Subnet ID": subnet_id,
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "ARN": arn,
                    "State": subnet.get('State', 'N/A'),
                    "VPC ID": subnet.get('VpcId', 'N/A'),
                    "CIDR Block": subnet.get('CidrBlock', 'N/A'),
                    "Availability Zone": subnet.get('AvailabilityZone', 'N/A'),
                    "Available IPs": subnet.get('AvailableIpAddressCount', 'N/A'),
                    "Auto-assign Public IP": 'Yes' if subnet.get('MapPublicIpOnLaunch') else 'No',
                    "Default for AZ": 'Yes' if subnet.get('DefaultForAz') else 'No',
                    "Tags": format_tags(tags)
                })
        
        return resources


class RouteTableScanner(BaseScanner):
    """Scanner for Route Tables"""
    
    resource_type = "Route Table"
    sheet_name = "Route Tables"
    
    def get_columns(self) -> List[str]:
        return [
            "Route Table Name",
            "Route Table ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "VPC ID",
            "Main",
            "Associated Subnets",
            "Number of Routes",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan Route Tables in the specified account/region"""
        resources = []
        ec2 = session.client('ec2', region_name=region)
        
        paginator = ec2.get_paginator('describe_route_tables')
        for page in paginator.paginate():
            for rt in page.get('RouteTables', []):
                rt_id = rt['RouteTableId']
                tags = rt.get('Tags', [])
                arn = f"arn:aws:ec2:{region}:{account_id}:route-table/{rt_id}"
                
                # Check if main route table
                is_main = 'No'
                associated_subnets = []
                for assoc in rt.get('Associations', []):
                    if assoc.get('Main'):
                        is_main = 'Yes'
                    if assoc.get('SubnetId'):
                        associated_subnets.append(assoc['SubnetId'])
                
                resources.append({
                    "Route Table Name": get_name_from_tags(tags),
                    "Route Table ID": rt_id,
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "ARN": arn,
                    "VPC ID": rt.get('VpcId', 'N/A'),
                    "Main": is_main,
                    "Associated Subnets": ", ".join(associated_subnets) if associated_subnets else "None",
                    "Number of Routes": len(rt.get('Routes', [])),
                    "Tags": format_tags(tags)
                })
        
        return resources
