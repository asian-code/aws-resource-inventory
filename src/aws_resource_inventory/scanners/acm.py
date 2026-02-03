"""ACM Certificate Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags


class ACMScanner(BaseScanner):
    """Scanner for ACM Certificates"""
    
    resource_type = "ACM Certificate"
    sheet_name = "ACM Certificates"
    
    def get_columns(self) -> List[str]:
        return [
            "Domain Name",
            "Certificate ARN",
            "Account ID",
            "Account Name",
            "Region",
            "Status",
            "Type",
            "Key Algorithm",
            "In Use By",
            "Not Before",
            "Not After",
            "Renewal Eligibility",
            "Created At",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan ACM certificates in the specified account/region"""
        resources = []
        acm = session.client('acm', region_name=region)
        
        paginator = acm.get_paginator('list_certificates')
        for page in paginator.paginate(Includes={'keyTypes': ['RSA_1024', 'RSA_2048', 'RSA_3072', 'RSA_4096', 'EC_prime256v1', 'EC_secp384r1', 'EC_secp521r1']}):
            for cert_summary in page.get('CertificateSummaryList', []):
                cert_arn = cert_summary['CertificateArn']
                
                # Get certificate details
                try:
                    cert_response = acm.describe_certificate(CertificateArn=cert_arn)
                    cert = cert_response.get('Certificate', {})
                    
                    # Get tags
                    tags = []
                    try:
                        tag_response = acm.list_tags_for_certificate(CertificateArn=cert_arn)
                        tags = tag_response.get('Tags', [])
                    except Exception:
                        pass
                    
                    # Get in-use resources
                    in_use_by = cert.get('InUseBy', [])
                    
                    resources.append({
                        "Domain Name": cert.get('DomainName', 'N/A'),
                        "Certificate ARN": cert_arn,
                        "Account ID": account_id,
                        "Account Name": account_name,
                        "Region": region,
                        "Status": cert.get('Status', 'N/A'),
                        "Type": cert.get('Type', 'N/A'),
                        "Key Algorithm": cert.get('KeyAlgorithm', 'N/A'),
                        "In Use By": str(len(in_use_by)) + " resources" if in_use_by else "Not in use",
                        "Not Before": str(cert.get('NotBefore', 'N/A')),
                        "Not After": str(cert.get('NotAfter', 'N/A')),
                        "Renewal Eligibility": cert.get('RenewalEligibility', 'N/A'),
                        "Created At": str(cert.get('CreatedAt', 'N/A')),
                        "Tags": format_tags(tags)
                    })
                except Exception:
                    continue
        
        return resources
