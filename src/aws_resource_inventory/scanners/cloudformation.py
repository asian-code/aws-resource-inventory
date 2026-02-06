"""CloudFormation Stack and StackSet Scanners"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, GlobalResourceScanner, format_tags, get_name_from_tags


class CloudFormationStackScanner(BaseScanner):
    """Scanner for CloudFormation Stacks"""
    
    resource_type = "CloudFormation Stack"
    sheet_name = "CloudFormationStacks"
    
    def get_columns(self) -> List[str]:
        return [
            "Stack Name",
            "Stack ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Status",
            "Creation Time",
            "Last Updated Time",
            "Description",
            "Root ID",
            "Parent ID",
            "Drift Status",
            "Enable Termination Protection",
            "Role ARN",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan CloudFormation stacks in the specified account/region"""
        resources = []
        cfn = session.client('cloudformation', region_name=region)
        
        try:
            paginator = cfn.get_paginator('describe_stacks')
            for page in paginator.paginate():
                for stack in page.get('Stacks', []):
                    tags = stack.get('Tags', [])
                    stack_name = stack['StackName']
                    stack_id = stack['StackId']
                    
                    # Get drift status if available
                    drift_status = stack.get('DriftInformation', {}).get('StackDriftStatus', 'NOT_CHECKED')
                    
                    resources.append({
                        "Stack Name": stack_name,
                        "Stack ID": stack_id,
                        "Account ID": account_id,
                        "Account Name": account_name,
                        "Region": region,
                        "ARN": stack_id,  # Stack ID is the ARN
                        "Status": stack.get('StackStatus', 'N/A'),
                        "Creation Time": str(stack.get('CreationTime', 'N/A')),
                        "Last Updated Time": str(stack.get('LastUpdatedTime', 'N/A')),
                        "Description": stack.get('Description', 'N/A'),
                        "Root ID": stack.get('RootId', 'N/A'),
                        "Parent ID": stack.get('ParentId', 'N/A'),
                        "Drift Status": drift_status,
                        "Enable Termination Protection": str(stack.get('EnableTerminationProtection', False)),
                        "Role ARN": stack.get('RoleARN', 'N/A'),
                        "Tags": format_tags(tags)
                    })
        except Exception as e:
            # Log but don't fail - some regions might not be enabled
            pass
        
        return resources


class CloudFormationStackSetScanner(GlobalResourceScanner):
    """Scanner for CloudFormation StackSets (Global resource - scanned from management region)"""
    
    resource_type = "CloudFormation StackSet"
    sheet_name = "CloudFormationStackSets"
    is_global = True  # StackSets are managed globally
    
    def get_columns(self) -> List[str]:
        return [
            "StackSet Name",
            "StackSet ID",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "Status",
            "Description",
            "Permission Model",
            "Auto Deployment Enabled",
            "Retain Stacks On Account Removal",
            "Drift Status",
            "Last Drift Check Time",
            "Managed Execution Active",
            "Organizational Unit IDs",
            "Regions",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan CloudFormation StackSets in the specified account"""
        resources = []
        cfn = session.client('cloudformation', region_name=region)
        
        try:
            # List all StackSets
            paginator = cfn.get_paginator('list_stack_sets')
            for page in paginator.paginate(Status='ACTIVE'):
                for stackset_summary in page.get('Summaries', []):
                    stackset_name = stackset_summary['StackSetName']
                    
                    # Get detailed StackSet information
                    try:
                        detail_response = cfn.describe_stack_set(StackSetName=stackset_name)
                        stackset = detail_response.get('StackSet', {})
                    except Exception:
                        # Use summary info if describe fails
                        stackset = stackset_summary
                    
                    tags = stackset.get('Tags', [])
                    
                    # Get auto deployment settings
                    auto_deployment = stackset.get('AutoDeployment', {})
                    auto_deployment_enabled = auto_deployment.get('Enabled', False)
                    retain_stacks = auto_deployment.get('RetainStacksOnAccountRemoval', False)
                    
                    # Get managed execution settings
                    managed_execution = stackset.get('ManagedExecution', {})
                    managed_execution_active = managed_execution.get('Active', False)
                    
                    # Get organizational unit IDs if available
                    org_unit_ids = stackset.get('OrganizationalUnitIds', [])
                    org_unit_ids_str = ', '.join(org_unit_ids) if org_unit_ids else 'N/A'
                    
                    # Get regions from stack instances (if we want to track where it's deployed)
                    regions_deployed = stackset.get('Regions', [])
                    regions_str = ', '.join(regions_deployed) if regions_deployed else 'N/A'
                    
                    resources.append({
                        "StackSet Name": stackset_name,
                        "StackSet ID": stackset.get('StackSetId', 'N/A'),
                        "Account ID": account_id,
                        "Account Name": account_name,
                        "Region": region,
                        "ARN": stackset.get('StackSetARN', 'N/A'),
                        "Status": stackset.get('Status', 'N/A'),
                        "Description": stackset.get('Description', 'N/A'),
                        "Permission Model": stackset.get('PermissionModel', 'SELF_MANAGED'),
                        "Auto Deployment Enabled": str(auto_deployment_enabled),
                        "Retain Stacks On Account Removal": str(retain_stacks),
                        "Drift Status": stackset.get('StackSetDriftDetectionDetails', {}).get('DriftStatus', 'NOT_CHECKED'),
                        "Last Drift Check Time": str(stackset.get('StackSetDriftDetectionDetails', {}).get('LastDriftCheckTimestamp', 'N/A')),
                        "Managed Execution Active": str(managed_execution_active),
                        "Organizational Unit IDs": org_unit_ids_str,
                        "Regions": regions_str,
                        "Tags": format_tags(tags)
                    })
        except Exception as e:
            # Log but don't fail
            pass
        
        return resources
