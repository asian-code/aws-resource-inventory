"""Scanner module initialization - exports all scanner classes"""

from .base import BaseScanner, GlobalResourceScanner, ScanResult, format_tags, get_name_from_tags, safe_get

# Compute Scanners
from .ec2 import EC2Scanner
from .lambda_functions import LambdaScanner
from .ecs import ECSServiceScanner, ECSTaskScanner
from .eks import EKSScanner
from .autoscaling import AutoScalingScanner

# Storage Scanners
from .s3 import S3Scanner
from .ebs import EBSScanner
from .efs import EFSScanner

# Database Scanners
from .rds import RDSScanner
from .dynamodb import DynamoDBScanner
from .elasticache import ElastiCacheScanner
from .redshift import RedshiftScanner

# Networking Scanners
from .vpc import VPCScanner, SubnetScanner, RouteTableScanner
from .security_groups import SecurityGroupScanner
from .nat_igw import NATGatewayScanner, InternetGatewayScanner
from .eip import EIPScanner
from .tgw import TransitGatewayAttachmentScanner

# Load Balancer Scanners
from .elb import ALBNLBScanner, ClassicELBScanner, TargetGroupScanner

# Identity Scanners
from .iam import IAMUserScanner, IAMRoleScanner, IAMPolicyScanner

# Security Scanners
from .kms import KMSScanner
from .secrets import SecretsManagerScanner
from .acm import ACMScanner

# Other Scanners
from .cloudwatch import CloudWatchAlarmScanner
from .sns import SNSScanner
from .sqs import SQSScanner
from .apigateway import APIGatewayScanner
from .cloudfront import CloudFrontScanner

# CloudFormation Scanners
from .cloudformation import CloudFormationStackScanner, CloudFormationStackSetScanner


# List of all available scanners (instantiated)
def get_all_scanners():
    """Return instances of all available scanners"""
    return [
        # Compute
        EC2Scanner(),
        LambdaScanner(),
        ECSServiceScanner(),
        ECSTaskScanner(),
        EKSScanner(),
        AutoScalingScanner(),
        
        # Storage
        S3Scanner(),
        EBSScanner(),
        EFSScanner(),
        
        # Database
        RDSScanner(),
        DynamoDBScanner(),
        ElastiCacheScanner(),
        RedshiftScanner(),
        
        # Networking
        VPCScanner(),
        SubnetScanner(),
        RouteTableScanner(),
        SecurityGroupScanner(),
        NATGatewayScanner(),
        InternetGatewayScanner(),
        EIPScanner(),
        TransitGatewayAttachmentScanner(),
        
        # Load Balancing
        ALBNLBScanner(),
        ClassicELBScanner(),
        TargetGroupScanner(),
        
        # Identity (Global)
        IAMUserScanner(),
        IAMRoleScanner(),
        IAMPolicyScanner(),
        
        # Security
        KMSScanner(),
        SecretsManagerScanner(),
        ACMScanner(),
        
        # Other
        CloudWatchAlarmScanner(),
        SNSScanner(),
        SQSScanner(),
        APIGatewayScanner(),
        CloudFrontScanner(),
        
        # CloudFormation
        CloudFormationStackScanner(),
        CloudFormationStackSetScanner(),
    ]


__all__ = [
    # Base classes
    'BaseScanner',
    'GlobalResourceScanner', 
    'ScanResult',
    'format_tags',
    'get_name_from_tags',
    'safe_get',
    'get_all_scanners',
    
    # Scanner classes
    'EC2Scanner',
    'LambdaScanner',
    'ECSServiceScanner',
    'ECSTaskScanner',
    'EKSScanner',
    'AutoScalingScanner',
    'S3Scanner',
    'EBSScanner',
    'EFSScanner',
    'RDSScanner',
    'DynamoDBScanner',
    'ElastiCacheScanner',
    'RedshiftScanner',
    'VPCScanner',
    'SubnetScanner',
    'RouteTableScanner',
    'SecurityGroupScanner',
    'NATGatewayScanner',
    'InternetGatewayScanner',
    'EIPScanner',
    'TransitGatewayAttachmentScanner',
    'ALBNLBScanner',
    'ClassicELBScanner',
    'TargetGroupScanner',
    'IAMUserScanner',
    'IAMRoleScanner',
    'IAMPolicyScanner',
    'KMSScanner',
    'SecretsManagerScanner',
    'ACMScanner',
    'CloudWatchAlarmScanner',
    'SNSScanner',
    'SQSScanner',
    'APIGatewayScanner',
    'CloudFrontScanner',
    'CloudFormationStackScanner',
    'CloudFormationStackSetScanner',
]
