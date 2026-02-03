"""Load Balancer Scanners (ALB, NLB, Classic ELB, Target Groups)"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags


class ALBNLBScanner(BaseScanner):
    """Scanner for Application and Network Load Balancers (ELBv2)"""
    
    resource_type = "ALB/NLB"
    sheet_name = "ALB-NLB"
    
    def get_columns(self) -> List[str]:
        return [
            "Load Balancer Name",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Type",
            "Scheme",
            "State",
            "DNS Name",
            "VPC ID",
            "Availability Zones",
            "Security Groups",
            "Created Time",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan ALBs and NLBs in the specified account/region"""
        resources = []
        elbv2 = session.client('elbv2', region_name=region)
        
        paginator = elbv2.get_paginator('describe_load_balancers')
        for page in paginator.paginate():
            for lb in page.get('LoadBalancers', []):
                lb_arn = lb['LoadBalancerArn']
                
                # Get tags
                tags = []
                try:
                    tag_response = elbv2.describe_tags(ResourceArns=[lb_arn])
                    for desc in tag_response.get('TagDescriptions', []):
                        tags = desc.get('Tags', [])
                except Exception:
                    pass
                
                # Get availability zones
                azs = [az.get('ZoneName', 'N/A') for az in lb.get('AvailabilityZones', [])]
                
                # Get security groups (only for ALB)
                security_groups = lb.get('SecurityGroups', [])
                
                resources.append({
                    "Load Balancer Name": lb.get('LoadBalancerName', 'N/A'),
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "ARN": lb_arn,
                    "Type": lb.get('Type', 'N/A'),
                    "Scheme": lb.get('Scheme', 'N/A'),
                    "State": lb.get('State', {}).get('Code', 'N/A'),
                    "DNS Name": lb.get('DNSName', 'N/A'),
                    "VPC ID": lb.get('VpcId', 'N/A'),
                    "Availability Zones": ", ".join(azs),
                    "Security Groups": ", ".join(security_groups) if security_groups else 'N/A',
                    "Created Time": str(lb.get('CreatedTime', 'N/A')),
                    "Tags": format_tags(tags)
                })
        
        return resources


class ClassicELBScanner(BaseScanner):
    """Scanner for Classic Load Balancers"""
    
    resource_type = "Classic ELB"
    sheet_name = "Classic ELB"
    
    def get_columns(self) -> List[str]:
        return [
            "Load Balancer Name",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "DNS Name",
            "Scheme",
            "VPC ID",
            "Availability Zones",
            "Subnets",
            "Security Groups",
            "Instances Count",
            "Created Time",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan Classic ELBs in the specified account/region"""
        resources = []
        elb = session.client('elb', region_name=region)
        
        paginator = elb.get_paginator('describe_load_balancers')
        for page in paginator.paginate():
            for lb in page.get('LoadBalancerDescriptions', []):
                lb_name = lb['LoadBalancerName']
                arn = f"arn:aws:elasticloadbalancing:{region}:{account_id}:loadbalancer/{lb_name}"
                
                # Get tags
                tags = []
                try:
                    tag_response = elb.describe_tags(LoadBalancerNames=[lb_name])
                    for desc in tag_response.get('TagDescriptions', []):
                        tags = desc.get('Tags', [])
                except Exception:
                    pass
                
                resources.append({
                    "Load Balancer Name": lb_name,
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "ARN": arn,
                    "DNS Name": lb.get('DNSName', 'N/A'),
                    "Scheme": lb.get('Scheme', 'N/A'),
                    "VPC ID": lb.get('VPCId', 'N/A'),
                    "Availability Zones": ", ".join(lb.get('AvailabilityZones', [])),
                    "Subnets": ", ".join(lb.get('Subnets', [])),
                    "Security Groups": ", ".join(lb.get('SecurityGroups', [])),
                    "Instances Count": len(lb.get('Instances', [])),
                    "Created Time": str(lb.get('CreatedTime', 'N/A')),
                    "Tags": format_tags(tags)
                })
        
        return resources


class TargetGroupScanner(BaseScanner):
    """Scanner for Target Groups"""
    
    resource_type = "Target Group"
    sheet_name = "Target Groups"
    
    def get_columns(self) -> List[str]:
        return [
            "Target Group Name",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Target Type",
            "Protocol",
            "Port",
            "VPC ID",
            "Health Check Protocol",
            "Health Check Path",
            "Load Balancer ARNs",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan Target Groups in the specified account/region"""
        resources = []
        elbv2 = session.client('elbv2', region_name=region)
        
        paginator = elbv2.get_paginator('describe_target_groups')
        for page in paginator.paginate():
            for tg in page.get('TargetGroups', []):
                tg_arn = tg['TargetGroupArn']
                
                # Get tags
                tags = []
                try:
                    tag_response = elbv2.describe_tags(ResourceArns=[tg_arn])
                    for desc in tag_response.get('TagDescriptions', []):
                        tags = desc.get('Tags', [])
                except Exception:
                    pass
                
                # Get associated load balancers
                lb_arns = tg.get('LoadBalancerArns', [])
                
                resources.append({
                    "Target Group Name": tg.get('TargetGroupName', 'N/A'),
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "ARN": tg_arn,
                    "Target Type": tg.get('TargetType', 'N/A'),
                    "Protocol": tg.get('Protocol', 'N/A'),
                    "Port": tg.get('Port', 'N/A'),
                    "VPC ID": tg.get('VpcId', 'N/A'),
                    "Health Check Protocol": tg.get('HealthCheckProtocol', 'N/A'),
                    "Health Check Path": tg.get('HealthCheckPath', 'N/A'),
                    "Load Balancer ARNs": "; ".join(lb_arns) if lb_arns else 'None',
                    "Tags": format_tags(tags)
                })
        
        return resources
