"""IAM Scanners (Users, Roles, Policies) - Global Resources"""

from typing import List, Dict, Any
import boto3
from .base import GlobalResourceScanner, format_tags


class IAMUserScanner(GlobalResourceScanner):
    """Scanner for IAM Users (Global resource)"""
    
    resource_type = "IAM User"
    sheet_name = "IAM Users"
    is_global = True
    
    def get_columns(self) -> List[str]:
        return [
            "User Name",
            "User ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Path",
            "Created Date",
            "Password Last Used",
            "MFA Enabled",
            "Access Keys",
            "Groups",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan IAM users in the specified account (global)"""
        resources = []
        iam = session.client('iam', region_name=region)
        
        paginator = iam.get_paginator('list_users')
        for page in paginator.paginate():
            for user in page.get('Users', []):
                user_name = user['UserName']
                
                # Get MFA devices
                mfa_enabled = 'No'
                try:
                    mfa_response = iam.list_mfa_devices(UserName=user_name)
                    if mfa_response.get('MFADevices'):
                        mfa_enabled = 'Yes'
                except Exception:
                    pass
                
                # Get access keys
                access_keys = 0
                try:
                    key_response = iam.list_access_keys(UserName=user_name)
                    access_keys = len(key_response.get('AccessKeyMetadata', []))
                except Exception:
                    pass
                
                # Get groups
                groups = []
                try:
                    group_response = iam.list_groups_for_user(UserName=user_name)
                    groups = [g['GroupName'] for g in group_response.get('Groups', [])]
                except Exception:
                    pass
                
                # Get tags
                tags = []
                try:
                    tag_response = iam.list_user_tags(UserName=user_name)
                    tags = tag_response.get('Tags', [])
                except Exception:
                    pass
                
                resources.append({
                    "User Name": user_name,
                    "User ID": user.get('UserId', 'N/A'),
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": "global",
                    "ARN": user.get('Arn', 'N/A'),
                    "Path": user.get('Path', '/'),
                    "Created Date": str(user.get('CreateDate', 'N/A')),
                    "Password Last Used": str(user.get('PasswordLastUsed', 'Never')),
                    "MFA Enabled": mfa_enabled,
                    "Access Keys": access_keys,
                    "Groups": ", ".join(groups) if groups else 'None',
                    "Tags": format_tags(tags)
                })
        
        return resources


class IAMRoleScanner(GlobalResourceScanner):
    """Scanner for IAM Roles (Global resource)"""
    
    resource_type = "IAM Role"
    sheet_name = "IAM Roles"
    is_global = True
    
    def get_columns(self) -> List[str]:
        return [
            "Role Name",
            "Role ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Path",
            "Created Date",
            "Max Session Duration",
            "Description",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan IAM roles in the specified account (global)"""
        resources = []
        iam = session.client('iam', region_name=region)
        
        paginator = iam.get_paginator('list_roles')
        for page in paginator.paginate():
            for role in page.get('Roles', []):
                role_name = role['RoleName']
                
                # Get tags
                tags = []
                try:
                    tag_response = iam.list_role_tags(RoleName=role_name)
                    tags = tag_response.get('Tags', [])
                except Exception:
                    pass
                
                resources.append({
                    "Role Name": role_name,
                    "Role ID": role.get('RoleId', 'N/A'),
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": "global",
                    "ARN": role.get('Arn', 'N/A'),
                    "Path": role.get('Path', '/'),
                    "Created Date": str(role.get('CreateDate', 'N/A')),
                    "Max Session Duration": role.get('MaxSessionDuration', 3600),
                    "Description": role.get('Description', 'N/A'),
                    "Tags": format_tags(tags)
                })
        
        return resources


class IAMPolicyScanner(GlobalResourceScanner):
    """Scanner for IAM Customer Managed Policies (Global resource)"""
    
    resource_type = "IAM Policy"
    sheet_name = "IAM Policies"
    is_global = True
    
    def get_columns(self) -> List[str]:
        return [
            "Policy Name",
            "Policy ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Path",
            "Default Version",
            "Attachment Count",
            "Is Attachable",
            "Created Date",
            "Updated Date",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan IAM customer managed policies in the specified account (global)"""
        resources = []
        iam = session.client('iam', region_name=region)
        
        # Only list customer managed policies (Scope='Local')
        paginator = iam.get_paginator('list_policies')
        for page in paginator.paginate(Scope='Local'):
            for policy in page.get('Policies', []):
                policy_arn = policy['Arn']
                
                # Get tags
                tags = []
                try:
                    tag_response = iam.list_policy_tags(PolicyArn=policy_arn)
                    tags = tag_response.get('Tags', [])
                except Exception:
                    pass
                
                resources.append({
                    "Policy Name": policy.get('PolicyName', 'N/A'),
                    "Policy ID": policy.get('PolicyId', 'N/A'),
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": "global",
                    "ARN": policy_arn,
                    "Path": policy.get('Path', '/'),
                    "Default Version": policy.get('DefaultVersionId', 'N/A'),
                    "Attachment Count": policy.get('AttachmentCount', 0),
                    "Is Attachable": 'Yes' if policy.get('IsAttachable') else 'No',
                    "Created Date": str(policy.get('CreateDate', 'N/A')),
                    "Updated Date": str(policy.get('UpdateDate', 'N/A')),
                    "Tags": format_tags(tags)
                })
        
        return resources
