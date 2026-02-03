"""ECS Service and Task Scanners"""

from typing import List, Dict, Any
import boto3
from .base import BaseScanner, format_tags


class ECSServiceScanner(BaseScanner):
    """Scanner for ECS Services"""
    
    resource_type = "ECS Service"
    sheet_name = "ECS Services"
    
    def get_columns(self) -> List[str]:
        return [
            "Service Name",
            "Service ARN",
            "Account ID",
            "Account Name",
            "Region",
            "Cluster ARN",
            "Status",
            "Launch Type",
            "Desired Count",
            "Running Count",
            "Task Definition",
            "Created At",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan ECS services in the specified account/region"""
        resources = []
        ecs = session.client('ecs', region_name=region)
        
        # List all clusters first
        cluster_paginator = ecs.get_paginator('list_clusters')
        clusters = []
        for page in cluster_paginator.paginate():
            clusters.extend(page.get('clusterArns', []))
        
        # For each cluster, list services
        for cluster_arn in clusters:
            service_paginator = ecs.get_paginator('list_services')
            service_arns = []
            
            for page in service_paginator.paginate(cluster=cluster_arn):
                service_arns.extend(page.get('serviceArns', []))
            
            if not service_arns:
                continue
            
            # Describe services in batches of 10 (API limit)
            for i in range(0, len(service_arns), 10):
                batch = service_arns[i:i+10]
                response = ecs.describe_services(
                    cluster=cluster_arn,
                    services=batch,
                    include=['TAGS']
                )
                
                for service in response.get('services', []):
                    tags = service.get('tags', [])
                    # Convert ECS tag format to standard format
                    formatted_tags = [{"Key": t.get('key', ''), "Value": t.get('value', '')} for t in tags]
                    
                    resources.append({
                        "Service Name": service.get('serviceName', 'N/A'),
                        "Service ARN": service.get('serviceArn', 'N/A'),
                        "Account ID": account_id,
                        "Account Name": account_name,
                        "Region": region,
                        "Cluster ARN": cluster_arn,
                        "Status": service.get('status', 'N/A'),
                        "Launch Type": service.get('launchType', 'N/A'),
                        "Desired Count": service.get('desiredCount', 0),
                        "Running Count": service.get('runningCount', 0),
                        "Task Definition": service.get('taskDefinition', 'N/A'),
                        "Created At": str(service.get('createdAt', 'N/A')),
                        "Tags": format_tags(formatted_tags)
                    })
        
        return resources


class ECSTaskScanner(BaseScanner):
    """Scanner for running ECS Tasks"""
    
    resource_type = "ECS Task"
    sheet_name = "ECS Tasks"
    
    def get_columns(self) -> List[str]:
        return [
            "Task ARN",
            "Account ID",
            "Account Name",
            "Region",
            "Cluster ARN",
            "Task Definition ARN",
            "Last Status",
            "Desired Status",
            "Launch Type",
            "CPU",
            "Memory",
            "Started At",
            "Connectivity",
            "Tags"
        ]
    
    def scan(self, session: boto3.Session, account_id: str, account_name: str, region: str) -> List[Dict[str, Any]]:
        """Scan running ECS tasks in the specified account/region"""
        resources = []
        ecs = session.client('ecs', region_name=region)
        
        # List all clusters first
        cluster_paginator = ecs.get_paginator('list_clusters')
        clusters = []
        for page in cluster_paginator.paginate():
            clusters.extend(page.get('clusterArns', []))
        
        # For each cluster, list tasks
        for cluster_arn in clusters:
            task_paginator = ecs.get_paginator('list_tasks')
            task_arns = []
            
            for page in task_paginator.paginate(cluster=cluster_arn):
                task_arns.extend(page.get('taskArns', []))
            
            if not task_arns:
                continue
            
            # Describe tasks in batches of 100 (API limit)
            for i in range(0, len(task_arns), 100):
                batch = task_arns[i:i+100]
                response = ecs.describe_tasks(
                    cluster=cluster_arn,
                    tasks=batch,
                    include=['TAGS']
                )
                
                for task in response.get('tasks', []):
                    tags = task.get('tags', [])
                    formatted_tags = [{"Key": t.get('key', ''), "Value": t.get('value', '')} for t in tags]
                    
                    resources.append({
                        "Task ARN": task.get('taskArn', 'N/A'),
                        "Account ID": account_id,
                        "Account Name": account_name,
                        "Region": region,
                        "Cluster ARN": cluster_arn,
                        "Task Definition ARN": task.get('taskDefinitionArn', 'N/A'),
                        "Last Status": task.get('lastStatus', 'N/A'),
                        "Desired Status": task.get('desiredStatus', 'N/A'),
                        "Launch Type": task.get('launchType', 'N/A'),
                        "CPU": task.get('cpu', 'N/A'),
                        "Memory": task.get('memory', 'N/A'),
                        "Started At": str(task.get('startedAt', 'N/A')),
                        "Connectivity": task.get('connectivity', 'N/A'),
                        "Tags": format_tags(formatted_tags)
                    })
        
        return resources
