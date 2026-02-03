"""CloudWatch Alarm Scanner"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags


class CloudWatchAlarmScanner(BaseScanner):
    """Scanner for CloudWatch Alarms"""
    
    resource_type = "CloudWatch Alarm"
    sheet_name = "CloudWatch Alarms"
    
    def get_columns(self) -> List[str]:
        return [
            "Alarm Name",
            "Account ID",
            "Account Name",
            "Region",
            "ARN",
            "State",
            "Metric Name",
            "Namespace",
            "Comparison Operator",
            "Threshold",
            "Period (sec)",
            "Evaluation Periods",
            "Actions Enabled",
            "Updated Time",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan CloudWatch alarms in the specified account/region"""
        resources = []
        cloudwatch = session.client('cloudwatch', region_name=region)
        
        paginator = cloudwatch.get_paginator('describe_alarms')
        for page in paginator.paginate():
            for alarm in page.get('MetricAlarms', []):
                alarm_name = alarm['AlarmName']
                alarm_arn = alarm.get('AlarmArn', f"arn:aws:cloudwatch:{region}:{account_id}:alarm:{alarm_name}")
                
                # Get tags
                tags = []
                try:
                    tag_response = cloudwatch.list_tags_for_resource(ResourceARN=alarm_arn)
                    tags = tag_response.get('Tags', [])
                except Exception:
                    pass
                
                resources.append({
                    "Alarm Name": alarm_name,
                    "Account ID": account_id,
                    "Account Name": account_name,
                    "Region": region,
                    "ARN": alarm_arn,
                    "State": alarm.get('StateValue', 'N/A'),
                    "Metric Name": alarm.get('MetricName', 'N/A'),
                    "Namespace": alarm.get('Namespace', 'N/A'),
                    "Comparison Operator": alarm.get('ComparisonOperator', 'N/A'),
                    "Threshold": alarm.get('Threshold', 'N/A'),
                    "Period (sec)": alarm.get('Period', 'N/A'),
                    "Evaluation Periods": alarm.get('EvaluationPeriods', 'N/A'),
                    "Actions Enabled": 'Yes' if alarm.get('ActionsEnabled') else 'No',
                    "Updated Time": str(alarm.get('StateUpdatedTimestamp', 'N/A')),
                    "Tags": format_tags(tags)
                })
        
        return resources
