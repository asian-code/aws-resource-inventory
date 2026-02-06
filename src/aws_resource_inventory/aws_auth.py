"""AWS OIDC and Cross-Account Role Authentication for Resource Inventory Tool"""

import boto3
from botocore.exceptions import ClientError
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class OIDCAuthenticator:
    """Handle AWS OIDC authentication and cross-account role assumption"""
    
    def __init__(self, cross_account_role_name: str = "AWSControlTowerExecution"):
        """
        Initialize the OIDC authenticator.
        
        Args:
            cross_account_role_name: The role name to assume in each target account
        """
        self.cross_account_role_name = cross_account_role_name
        self._management_session = None
        self._org_client = None
    
    @property
    def management_session(self) -> boto3.Session:
        """Get the management account session (uses environment credentials from OIDC)"""
        if self._management_session is None:
            # Uses credentials from environment (set by GitHub Actions OIDC)
            self._management_session = boto3.Session()
        return self._management_session
    
    @property
    def org_client(self):
        """Get Organizations client for the management account"""
        if self._org_client is None:
            self._org_client = self.management_session.client('organizations')
        return self._org_client
    
    def authenticate(self) -> bool:
        """Verify that we have valid AWS credentials (compatibility method)"""
        return self.verify_credentials()
    
    def verify_credentials(self) -> bool:
        """Verify that we have valid AWS credentials"""
        try:
            sts = self.management_session.client('sts')
            identity = sts.get_caller_identity()
            logger.info(f"Authenticated as: {identity['Arn']}")
            logger.info(f"Account: {identity['Account']}")
            return True
        except Exception as e:
            logger.error(f"Failed to verify credentials: {e}")
            return False
    
    def list_accounts(self) -> Dict[str, str]:
        """
        List all AWS accounts in the organization.
        
        Returns:
            Dictionary of {account_id: account_name}
        """
        accounts = {}
        
        try:
            paginator = self.org_client.get_paginator('list_accounts')
            for page in paginator.paginate():
                for account in page.get('Accounts', []):
                    # Skip suspended accounts
                    if account.get('Status') == 'ACTIVE':
                        accounts[account['Id']] = account['Name']
            
            logger.info(f"Found {len(accounts)} active accounts in organization")
            return accounts
            
        except ClientError as e:
            logger.error(f"Failed to list accounts: {e}")
            raise
    
    def get_account_credentials(self, account_id: str) -> Optional[Dict[str, str]]:
        """
        Get temporary credentials for a target account by assuming the cross-account role.
        
        Args:
            account_id: The AWS account ID to get credentials for
            
        Returns:
            Dictionary with aws_access_key_id, aws_secret_access_key, aws_session_token
            or None if role assumption failed
        """
        try:
            sts = self.management_session.client('sts')
            
            role_arn = f"arn:aws:iam::{account_id}:role/{self.cross_account_role_name}"
            
            response = sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName=f"resource-inventory-{account_id}",
                DurationSeconds=3600  # 1 hour
            )
            
            creds = response['Credentials']
            return {
                'aws_access_key_id': creds['AccessKeyId'],
                'aws_secret_access_key': creds['SecretAccessKey'],
                'aws_session_token': creds['SessionToken']
            }
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'AccessDenied':
                logger.debug(f"Access denied assuming role in account {account_id}: {e}")
            else:
                logger.warning(f"Failed to assume role in account {account_id}: {e}")
            return None
    
    def get_session_for_account(self, account_id: str) -> Optional[boto3.Session]:
        """
        Get a boto3 Session for a target account.
        
        Args:
            account_id: The AWS account ID
            
        Returns:
            boto3.Session configured for the target account, or None if failed
        """
        creds = self.get_account_credentials(account_id)
        if not creds:
            return None
        
        return boto3.Session(
            aws_access_key_id=creds['aws_access_key_id'],
            aws_secret_access_key=creds['aws_secret_access_key'],
            aws_session_token=creds['aws_session_token']
        )


# Keep backwards compatibility alias
SSOAuthenticator = OIDCAuthenticator
