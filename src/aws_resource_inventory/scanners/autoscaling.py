"""Auto Scaling Group Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags


class AutoScalingScanner(BaseScanner):
    """Scanner for Auto Scaling Groups"""
    
    resource_type = "Auto Scaling Group"
    sheet_name = "Auto Scaling Groups"
    
    def get_columns(self) -> List[str]:
        return [
            "ASG Name",
            "ASG ARN",
            "Account ID",
            "Account Name",
            "Region",
            "Status",
            "Min Size",
            "Max Size",
            "Desired Capacity",
            "Current Instances",
            "Launch Template/Config",
            "Availability Zones",
            "Health Check Type",
            "Created Time",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan Auto Scaling Groups in the specified account/region"""
        resources = []
        autoscaling = session.client('autoscaling', region_name=region)
        
        paginator = autoscaling.get_paginator('describe_auto_scaling_groups')
        for page in paginator.paginate():
            for asg in page.get('AutoScalingGroups', []):
                tags = asg.get('Tags', [])
                formatted_tags = [{"Key": t.get('Key', ''), "Value": t.get('Value', '')} for t in tags]
                
                # Get launch template or launch configuration
                launch_config = 'N/A'
                if asg.get('LaunchTemplate'):
                    lt = asg['LaunchTemplate']
                    launch_config = f"Template: {lt.get('LaunchTemplateName', lt.get('LaunchTemplateId', 'N/A'))}"
                elif asg.get('LaunchConfigurationName'):
                    launch_config = f"Config: {asg['LaunchConfigurationName']}"
                elif asg.get('MixedInstancesPolicy'):
                    lt = asg['MixedInstancesPolicy'].get('LaunchTemplate', {}).get('LaunchTemplateSpecification', {})
                    launch_config = f"Mixed: {lt.get('LaunchTemplateName', lt.get('LaunchTemplateId', 'N/A'))}"
                
                resources.append({
                    "ASG Name": asg.get('AutoScalingGroupName', 'N/A'),
                    "ASG ARN": asg.get('AutoScalingGroupARN', 'N/A'),
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "Status": asg.get('Status', 'Active'),
                    "Min Size": asg.get('MinSize', 0),
                    "Max Size": asg.get('MaxSize', 0),
                    "Desired Capacity": asg.get('DesiredCapacity', 0),
                    "Current Instances": len(asg.get('Instances', [])),
                    "Launch Template/Config": launch_config,
                    "Availability Zones": ", ".join(asg.get('AvailabilityZones', [])),
                    "Health Check Type": asg.get('HealthCheckType', 'N/A'),
                    "Created Time": str(asg.get('CreatedTime', 'N/A')),
                    "Tags": format_tags(formatted_tags)
                })
        
        return resources
