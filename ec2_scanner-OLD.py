#!/usr/bin/env python3
"""
EC2 Inventory Tool - Scan all EC2 instances across AWS Organization
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple
import sys

import boto3
from botocore.exceptions import ClientError
import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from openpyxl.utils import get_column_letter

from aws_auth import SSOAuthenticator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ec2-inventory.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
console = Console()


class EC2InventoryScanner:
    """Scan EC2 instances across AWS Organization"""
    
    def __init__(self, config_path: str = 'sso-config.json'):
        """Initialize scanner with configuration"""
        self.config = self._load_config(config_path)
        self.target_regions = self.config.get('target_regions', ['us-east-1', 'us-west-2'])
        self.max_workers = self.config.get('max_workers', 20)
        self.output_dir = Path(self.config.get('output_dir', 'output'))
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize authenticator
        self.authenticator = SSOAuthenticator(
            sso_start_url=self.config['sso_start_url'],
            sso_region=self.config['sso_region'],
            role_name=self.config['role_name']
        )
        
        # Results storage
        self.instances = []
        self.skipped_accounts = []
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            console.print(f"[red]Error: Configuration file '{config_path}' not found[/red]")
            sys.exit(1)
        except json.JSONDecodeError as e:
            console.print(f"[red]Error: Invalid JSON in configuration file: {e}[/red]")
            sys.exit(1)
    
    def scan_account_region(self, account_id: str, account_name: str, region: str, credentials: dict) -> Tuple[List[Dict], Optional[str]]:
        """Scan EC2 instances in a specific account and region"""
        instances = []
        error = None
        
        try:
            # Create EC2 client with temporary credentials
            ec2 = boto3.client(
                'ec2',
                region_name=region,
                aws_access_key_id=credentials['aws_access_key_id'],
                aws_secret_access_key=credentials['aws_secret_access_key'],
                aws_session_token=credentials['aws_session_token']
            )
            
            # Describe all instances
            paginator = ec2.get_paginator('describe_instances')
            for page in paginator.paginate():
                for reservation in page.get('Reservations', []):
                    for instance in reservation.get('Instances', []):
                        # Extract instance name from tags
                        instance_name = None
                        if instance.get('Tags'):
                            for tag in instance['Tags']:
                                if tag['Key'] == 'Name':
                                    instance_name = tag['Value']
                                    break
                        
                        # Get IAM instance profile ARN
                        iam_role_arn = None
                        if instance.get('IamInstanceProfile'):
                            iam_role_arn = instance['IamInstanceProfile'].get('Arn', 'None')
                        else:
                            iam_role_arn = 'None'
                        
                        # Get IPs
                        private_ip = instance.get('PrivateIpAddress', 'N/A')
                        public_ip = instance.get('PublicIpAddress', 'N/A')
                        
                        # Build instance record
                        instance_data = {
                            'Instance Name': instance_name or 'N/A',
                            'Instance ID': instance['InstanceId'],
                            'Account ID': account_id,
                            'Account Name': account_name,
                            'Region': region,
                            'Instance State': instance['State']['Name'],
                            'Instance Type': instance['InstanceType'],
                            'IAM Role/Instance Profile ARN': iam_role_arn,
                            'Private IP': private_ip,
                            'Public IP': public_ip
                        }
                        
                        instances.append(instance_data)
            
            logger.debug(f"Found {len(instances)} instances in {account_id}/{region}")
            
        except ClientError as e:
            error = f"{account_id} ({account_name}) - {region}: {str(e)}"
            logger.warning(f"Failed to scan {account_id}/{region}: {e}")
        except Exception as e:
            error = f"{account_id} ({account_name}) - {region}: {str(e)}"
            logger.error(f"Unexpected error scanning {account_id}/{region}: {e}")
        
        return instances, error
    
    def scan_account(self, account_id: str, account_name: str) -> Tuple[List[Dict], List[str]]:
        """Scan all target regions in an account"""
        all_instances = []
        errors = []
        
        # Get credentials for this account
        credentials = self.authenticator.get_account_credentials(account_id)
        if not credentials:
            error = f"{account_id} ({account_name}): Failed to get credentials"
            logger.warning(error)
            return [], [error]
        
        # Scan each region
        for region in self.target_regions:
            instances, error = self.scan_account_region(account_id, account_name, region, credentials)
            all_instances.extend(instances)
            if error:
                errors.append(error)
        
        return all_instances, errors
    
    def scan_all_accounts(self):
        """Scan all accounts in the organization"""
        console.print("\n[bold cyan]🔍 Starting EC2 Inventory Scan[/bold cyan]\n")
        
        # Authenticate
        console.print("[yellow]Authenticating with AWS SSO...[/yellow]")
        if not self.authenticator.authenticate():
            console.print("[red]Authentication failed. Exiting.[/red]")
            sys.exit(1)
        
        # Get list of accounts
        console.print("[yellow]Fetching AWS Organization accounts...[/yellow]")
        accounts = self.authenticator.list_accounts()
        console.print(f"[green]Found {len(accounts)} accounts to scan[/green]\n")
        
        # Scan accounts in parallel
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task(
                f"[cyan]Scanning {len(accounts)} accounts across {len(self.target_regions)} regions...",
                total=len(accounts)
            )
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all account scan tasks
                future_to_account = {
                    executor.submit(self.scan_account, account_id, account_name): (account_id, account_name)
                    for account_id, account_name in accounts.items()
                }
                
                # Process results as they complete
                for future in as_completed(future_to_account):
                    account_id, account_name = future_to_account[future]
                    try:
                        instances, errors = future.result()
                        self.instances.extend(instances)
                        if errors:
                            self.skipped_accounts.extend(errors)
                    except Exception as e:
                        error = f"{account_id} ({account_name}): Unexpected error: {str(e)}"
                        self.skipped_accounts.append(error)
                        logger.error(error)
                    
                    progress.update(task, advance=1)
        
        console.print(f"\n[green]✅ Scan complete![/green]")
        console.print(f"   Total instances found: [bold]{len(self.instances)}[/bold]")
        console.print(f"   Accounts/regions scanned: [bold]{len(accounts) * len(self.target_regions)}[/bold]")
        
        if self.skipped_accounts:
            console.print(f"   [yellow]Skipped/Failed: {len(self.skipped_accounts)}[/yellow]")
    
    def export_to_excel(self):
        """Export results to Excel file"""
        if not self.instances:
            console.print("\n[yellow]No instances found. Skipping Excel export.[/yellow]")
            return
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        output_file = self.output_dir / f'ec2-inventory-{timestamp}.xlsx'
        
        console.print(f"\n[yellow]Exporting to Excel...[/yellow]")
        
        # Create DataFrame
        df = pd.DataFrame(self.instances)
        
        # Sort by Account Name, Region, Instance Name
        df = df.sort_values(['Account Name', 'Region', 'Instance Name'])
        
        # Write to Excel with formatting
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='EC2 Inventory')
            
            # Get the worksheet
            worksheet = writer.sheets['EC2 Inventory']
            
            # Auto-adjust column widths
            for idx, col in enumerate(df.columns, 1):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                column_letter = get_column_letter(idx)
                worksheet.column_dimensions[column_letter].width = min(max_length, 50)
            
            # Add autofilter
            worksheet.auto_filter.ref = worksheet.dimensions
        
        console.print(f"[green]✅ Excel file created: {output_file}[/green]")
        
        # Display summary table
        self._display_summary()
    
    def _display_summary(self):
        """Display summary statistics"""
        if not self.instances:
            return
        
        df = pd.DataFrame(self.instances)
        
        console.print("\n[bold cyan]📊 Summary Statistics[/bold cyan]\n")
        
        # Instances by account
        table = Table(title="Instances by Account", show_header=True, header_style="bold magenta")
        table.add_column("Account Name", style="cyan")
        table.add_column("Account ID", style="yellow")
        table.add_column("Count", justify="right", style="green")
        
        account_counts = df.groupby(['Account Name', 'Account ID']).size().reset_index(name='Count')
        account_counts = account_counts.sort_values('Count', ascending=False)
        
        if len(account_counts) == 0:
            table.add_row("No data", "N/A", "0")
        else:
            for _, row in account_counts.head(10).iterrows():
                table.add_row(row['Account Name'], row['Account ID'], str(row['Count']))
        
        console.print(table)
        
        # Instances by region
        console.print()
        table2 = Table(title="Instances by Region", show_header=True, header_style="bold magenta")
        table2.add_column("Region", style="cyan")
        table2.add_column("Count", justify="right", style="green")
        
        region_counts = df['Region'].value_counts()
        for region, count in region_counts.items():
            table2.add_row(region, str(count))
        
        console.print(table2)
        
        # Instance states
        console.print()
        table3 = Table(title="Instance States", show_header=True, header_style="bold magenta")
        table3.add_column("State", style="cyan")
        table3.add_column("Count", justify="right", style="green")
        
        state_counts = df['Instance State'].value_counts()
        for state, count in state_counts.items():
            table3.add_row(state, str(count))
        
        console.print(table3)
    
    def display_skipped_accounts(self):
        """Display accounts/regions that were skipped"""
        if not self.skipped_accounts:
            console.print("\n[green]✅ All accounts/regions scanned successfully![/green]\n")
            return
        
        console.print("\n[bold yellow]⚠️  Skipped Accounts/Regions:[/bold yellow]\n")
        
        for error in self.skipped_accounts:
            console.print(f"  [red]•[/red] {error}")
        
        console.print()
    
    def run(self):
        """Main execution method"""
        try:
            self.scan_all_accounts()
            self.export_to_excel()
            self.display_skipped_accounts()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Scan interrupted by user.[/yellow]")
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[red]Fatal error: {e}[/red]")
            logger.exception("Fatal error occurred")
            sys.exit(1)


def main():
    """Entry point"""
    scanner = EC2InventoryScanner()
    scanner.run()


if __name__ == '__main__':
    main()
