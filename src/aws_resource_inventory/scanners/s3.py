"""S3 Bucket Scanner (Global Resource)"""

from typing import List, Dict, Any
import boto3
from .base import GlobalResourceScanner, format_tags


class S3Scanner(GlobalResourceScanner):
    """Scanner for S3 Buckets (Global resource - scanned once per account)"""
    
    resource_type = "S3 Bucket"
    sheet_name = "S3 Buckets"
    is_global = True
    
    def get_columns(self) -> List[str]:
        return [
            "Bucket Name",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Creation Date",
            "Versioning",
            "Encryption",
            "Public Access Block",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan S3 buckets in the specified account (global)"""
        resources = []
        s3 = session.client('s3', region_name=region)
        
        # List all buckets
        response = s3.list_buckets()
        
        for bucket in response.get('Buckets', []):
            bucket_name = bucket['Name']
            arn = f"arn:aws:s3:::{bucket_name}"
            
            # Get bucket location
            bucket_region = 'us-east-1'  # Default
            try:
                location = s3.get_bucket_location(Bucket=bucket_name)
                bucket_region = location.get('LocationConstraint') or 'us-east-1'
            except Exception:
                pass
            
            # Get versioning status
            versioning = 'Disabled'
            try:
                vers_response = s3.get_bucket_versioning(Bucket=bucket_name)
                versioning = vers_response.get('Status', 'Disabled')
            except Exception:
                pass
            
            # Get encryption
            encryption = 'None'
            try:
                enc_response = s3.get_bucket_encryption(Bucket=bucket_name)
                rules = enc_response.get('ServerSideEncryptionConfiguration', {}).get('Rules', [])
                if rules:
                    sse = rules[0].get('ApplyServerSideEncryptionByDefault', {})
                    encryption = sse.get('SSEAlgorithm', 'None')
            except s3.exceptions.ClientError as e:
                if e.response['Error']['Code'] != 'ServerSideEncryptionConfigurationNotFoundError':
                    pass
            except Exception:
                pass
            
            # Get public access block
            public_block = 'Not Configured'
            try:
                pab_response = s3.get_public_access_block(Bucket=bucket_name)
                config = pab_response.get('PublicAccessBlockConfiguration', {})
                if all([
                    config.get('BlockPublicAcls'),
                    config.get('IgnorePublicAcls'),
                    config.get('BlockPublicPolicy'),
                    config.get('RestrictPublicBuckets')
                ]):
                    public_block = 'All Blocked'
                else:
                    public_block = 'Partial'
            except Exception:
                pass
            
            # Get tags
            tags = []
            try:
                tag_response = s3.get_bucket_tagging(Bucket=bucket_name)
                tags = tag_response.get('TagSet', [])
            except Exception:
                pass
            
            resources.append({
                "Bucket Name": bucket_name,
                "Account ID": account_id,
                "Account Name": account_name,
                "Region": bucket_region,
                "ARN": arn,
                "Creation Date": str(bucket.get('CreationDate', 'N/A')),
                "Versioning": versioning,
                "Encryption": encryption,
                "Public Access Block": public_block,
                "Tags": format_tags(tags)
            })
        
        return resources
