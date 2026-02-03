"""AWS SSO authentication utilities for EC2 inventory tool"""

import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timezone
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SSOAuthenticator:
    """Handle AWS SSO authentication"""
    
    def __init__(self, sso_start_url: str, sso_region: str, role_name: str):
        self.sso_start_url = sso_start_url
        self.sso_region = sso_region
        self.role_name = role_name
        self.access_token = None
        
    def authenticate(self):
        """Authenticate via AWS SSO and get access token"""
        try:
            sso_oidc = boto3.client('sso-oidc', region_name=self.sso_region)
            
            # Register the client
            client_creds = sso_oidc.register_client(
                clientName='ec2-inventory-tool',
                clientType='public'
            )
            
            # Start device authorization
            device_auth = sso_oidc.start_device_authorization(
                clientId=client_creds['clientId'],
                clientSecret=client_creds['clientSecret'],
                startUrl=self.sso_start_url
            )
            
            # Display URL to user
            print(f"\n🔐 Please authorize this application:")
            print(f"   URL: {device_auth['verificationUriComplete']}")
            print(f"   Code: {device_auth['userCode']}")
            print(f"\n   Waiting for authorization...")
            
            # Poll for token
            import time
            interval = device_auth['interval']
            expires_at = time.time() + device_auth['expiresIn']
            
            while time.time() < expires_at:
                time.sleep(interval)
                try:
                    token_response = sso_oidc.create_token(
                        clientId=client_creds['clientId'],
                        clientSecret=client_creds['clientSecret'],
                        grantType='urn:ietf:params:oauth:grant-type:device_code',
                        deviceCode=device_auth['deviceCode']
                    )
                    self.access_token = token_response['accessToken']
                    print("✅ Authentication successful!\n")
                    return True
                except sso_oidc.exceptions.AuthorizationPendingException:
                    continue
                except Exception as e:
                    logger.error(f"Token creation failed: {e}")
                    return False
                    
            print("❌ Authentication timed out")
            return False
            
        except Exception as e:
            logger.error(f"SSO authentication failed: {e}")
            return False
    
    def list_accounts(self):
        """List all AWS accounts accessible via SSO"""
        if not self.access_token:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            sso = boto3.client('sso', region_name=self.sso_region)
            accounts = {}
            
            paginator = sso.get_paginator('list_accounts')
            for page in paginator.paginate(accessToken=self.access_token):
                for account in page.get('accountList', []):
                    accounts[account['accountId']] = account['accountName']
            
            logger.info(f"Found {len(accounts)} accounts")
            return accounts
            
        except ClientError as e:
            logger.error(f"Failed to list accounts: {e}")
            raise
    
    def get_account_credentials(self, account_id: str):
        """Get temporary credentials for an account"""
        if not self.access_token:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        try:
            sso = boto3.client('sso', region_name=self.sso_region)
            
            # Get role credentials
            response = sso.get_role_credentials(
                accessToken=self.access_token,
                accountId=account_id,
                roleName=self.role_name
            )
            
            creds = response['roleCredentials']
            return {
                'aws_access_key_id': creds['accessKeyId'],
                'aws_secret_access_key': creds['secretAccessKey'],
                'aws_session_token': creds['sessionToken']
            }
            
        except ClientError as e:
            logger.debug(f"Failed to get credentials for account {account_id}: {e}")
            return None
