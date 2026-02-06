#!/usr/bin/env python3
"""
AWS Resource Inventory Tool
Scan all resources across an entire AWS Organization and export to Excel.
"""

import sys
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
from collections import defaultdict
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.table import Table
from rich.panel import Panel

from aws_resource_inventory.config import load_config, Config
from aws_resource_inventory.aws_auth import OIDCAuthenticator
from aws_resource_inventory.scanners import get_all_scanners, ScanResult
from aws_resource_inventory.excel_exporter import create_inventory_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('aws-inventory.log')
    ]
)
logger = logging.getLogger(__name__)
console = Console()


class AWSResourceInventory:
    """Main orchestrator for scanning AWS resources across an organization"""
    
    def __init__(self, config_path: str = 'inventory-config.json'):
        """Initialize the inventory scanner"""
        self.config = load_config(config_path)
        
        # Initialize OIDC authenticator with cross-account role
        self.authenticator = OIDCAuthenticator(
            cross_account_role_name=self.config.cross_account_role_name
        )
        
        # Get all available scanners
        self.scanners = get_all_scanners()
        
        # Results storage
        self.results: Dict[str, ScanResult] = {}
        self.all_errors: List[str] = []
        self.accounts_scanned = 0
        self.output_files: List[Path] = []
    
    def _scan_account(
        self, 
        account_id: str, 
        account_name: str,
        credentials: dict
    ) -> Tuple[Dict[str, List], List[str]]:
        """
        Scan all resources in a single account.
        
        Returns:
            Tuple of (resources_by_scanner, errors)
        """
        resources_by_scanner = defaultdict(list)
        errors = []
        
        for scanner in self.scanners:
            scanner_name = scanner.sheet_name
            
            if scanner.is_global:
                # Global resources - scan once with first region
                region = self.config.target_regions[0]
                resources, error = scanner.scan_account_region(
                    credentials, account_id, account_name, region
                )
                resources_by_scanner[scanner_name].extend(resources)
                if error:
                    errors.append(error)
            else:
                # Regional resources - scan all target regions
                for region in self.config.target_regions:
                    resources, error = scanner.scan_account_region(
                        credentials, account_id, account_name, region
                    )
                    resources_by_scanner[scanner_name].extend(resources)
                    if error:
                        errors.append(error)
        
        return dict(resources_by_scanner), errors
    
    def scan_organization(self):
        """Scan all accounts in the organization"""
        console.print(Panel.fit(
            "[bold cyan]🔍 AWS Resource Inventory Scanner[/bold cyan]\n"
            f"Scanning {len(self.scanners)} resource types across {len(self.config.target_regions)} regions",
            border_style="cyan"
        ))
        
        # Verify credentials (OIDC credentials from environment)
        console.print("\n[yellow]🔐 Verifying AWS credentials...[/yellow]")
        if not self.authenticator.verify_credentials():
            console.print("[red]❌ Credential verification failed. Exiting.[/red]")
            sys.exit(1)
        console.print("[green]✅ AWS credentials verified[/green]")
        
        # Get list of accounts from Organizations
        console.print("[yellow]📋 Fetching AWS Organization accounts...[/yellow]")
        all_accounts = self.authenticator.list_accounts()
        
        # Apply blacklist filter
        accounts = self.config.filter_accounts(all_accounts)
        blacklisted_count = len(all_accounts) - len(accounts)
        
        console.print(f"[green]✅ Found {len(all_accounts)} accounts[/green]")
        if blacklisted_count > 0:
            console.print(f"[yellow]⚠️  {blacklisted_count} accounts excluded by blacklist[/yellow]")
        console.print(f"[cyan]📊 Scanning {len(accounts)} accounts...[/cyan]\n")
        
        # Initialize results storage for each scanner
        for scanner in self.scanners:
            self.results[scanner.sheet_name] = ScanResult(
                resource_type=scanner.resource_type,
                sheet_name=scanner.sheet_name,
                resources=[],
                errors=[],
                is_global=scanner.is_global
            )
        
        # Scan accounts in parallel
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False
        ) as progress:
            
            task = progress.add_task(
                f"[cyan]Scanning {len(accounts)} accounts...",
                total=len(accounts)
            )
            
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                # Submit account scanning tasks
                future_to_account = {}
                
                for account_id, account_name in accounts.items():
                    # Get credentials for each account
                    credentials = self.authenticator.get_account_credentials(account_id)
                    
                    if not credentials:
                        self.all_errors.append(
                            f"Failed to get credentials for {account_id} ({account_name})"
                        )
                        progress.update(task, advance=1)
                        continue
                    
                    future = executor.submit(
                        self._scan_account,
                        account_id,
                        account_name,
                        credentials
                    )
                    future_to_account[future] = (account_id, account_name)
                
                # Process results as they complete
                for future in as_completed(future_to_account):
                    account_id, account_name = future_to_account[future]
                    
                    try:
                        resources_by_scanner, errors = future.result()
                        
                        # Merge resources into results
                        for scanner_name, resources in resources_by_scanner.items():
                            self.results[scanner_name].resources.extend(resources)
                        
                        # Collect errors
                        self.all_errors.extend(errors)
                        self.accounts_scanned += 1
                        
                    except Exception as e:
                        error_msg = f"Unexpected error scanning {account_id} ({account_name}): {str(e)}"
                        self.all_errors.append(error_msg)
                        logger.error(error_msg)
                    
                    progress.update(task, advance=1)
        
        console.print(f"\n[green]✅ Scan complete![/green]")
        self._display_summary()
    
    def _display_summary(self):
        """Display summary statistics"""
        console.print("\n[bold cyan]📊 Resource Summary[/bold cyan]\n")
        
        # Create summary table
        table = Table(
            title="Resources Found",
            show_header=True,
            header_style="bold magenta",
            border_style="cyan"
        )
        table.add_column("Resource Type", style="cyan", min_width=25)
        table.add_column("Count", justify="right", style="green", min_width=10)
        table.add_column("Global", justify="center", min_width=8)
        
        total_resources = 0
        for scanner in self.scanners:
            result = self.results.get(scanner.sheet_name)
            if result:
                count = len(result.resources)
                total_resources += count
                if count > 0:  # Only show non-empty resource types
                    table.add_row(
                        result.resource_type,
                        str(count),
                        "✓" if result.is_global else ""
                    )
        
        console.print(table)
        
        # Summary stats
        console.print(f"\n[bold]Total Resources:[/bold] [green]{total_resources}[/green]")
        console.print(f"[bold]Accounts Scanned:[/bold] [cyan]{self.accounts_scanned}[/cyan]")
        console.print(f"[bold]Regions Scanned:[/bold] [cyan]{len(self.config.target_regions)}[/cyan]")
        
        if self.all_errors:
            console.print(f"[bold]Errors/Skipped:[/bold] [yellow]{len(self.all_errors)}[/yellow]")
    
    def export_to_excel(self) -> List[Path]:
        """Export results to Excel files"""
        # Convert results dict to list
        results_list = list(self.results.values())
        
        self.output_files = create_inventory_report(
            results=results_list,
            errors=self.all_errors,
            output_dir=self.config.output_dir,
            accounts_scanned=self.accounts_scanned,
            regions_scanned=len(self.config.target_regions)
        )
        
        return self.output_files
    
    def upload_to_s3(self) -> bool:
        """Upload output files to S3 bucket if configured"""
        if not self.config.s3_bucket:
            console.print("[yellow]ℹ️  S3 bucket not configured, skipping upload[/yellow]")
            return False
        
        if not self.output_files:
            console.print("[yellow]⚠️  No files to upload[/yellow]")
            return False
        
        import boto3
        s3 = boto3.client('s3')
        
        console.print(f"\n[yellow]☁️  Uploading files to s3://{self.config.s3_bucket}/{self.config.s3_prefix}[/yellow]")
        
        uploaded = 0
        for file_path in self.output_files:
            try:
                s3_key = f"{self.config.s3_prefix}{file_path.name}" if self.config.s3_prefix else file_path.name
                s3.upload_file(str(file_path), self.config.s3_bucket, s3_key)
                console.print(f"  ✅ Uploaded: {file_path.name}")
                uploaded += 1
            except Exception as e:
                console.print(f"  ❌ Failed to upload {file_path.name}: {e}")
        
        console.print(f"[green]✅ Uploaded {uploaded}/{len(self.output_files)} files to S3[/green]")
        return uploaded == len(self.output_files)
    
    def display_errors(self):
        """Display any errors that occurred during scanning"""
        if not self.all_errors:
            console.print("\n[green]✅ All accounts and regions scanned successfully![/green]")
            return
        
        console.print(f"\n[bold yellow]⚠️  {len(self.all_errors)} Errors/Skipped:[/bold yellow]")
        
        # Group errors by type
        for i, error in enumerate(self.all_errors[:20], 1):  # Show first 20
            console.print(f"  [red]{i}.[/red] {error}")
        
        if len(self.all_errors) > 20:
            console.print(f"\n  [yellow]... and {len(self.all_errors) - 20} more (see Excel report for full list)[/yellow]")
    
    def run(self):
        """Main execution method"""
        try:
            start_time = datetime.now()
            
            # Scan all resources
            self.scan_organization()
            
            # Export to Excel
            self.export_to_excel()
            
            # Upload to S3 if configured
            if self.config.s3_bucket:
                self.upload_to_s3()
            
            # Display errors
            self.display_errors()
            
            # Execution time
            elapsed = datetime.now() - start_time
            console.print(f"\n[bold cyan]⏱️  Total execution time: {elapsed}[/bold cyan]\n")
            
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️  Scan interrupted by user.[/yellow]")
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[red]❌ Fatal error: {e}[/red]")
            logger.exception("Fatal error occurred")
            sys.exit(1)


def main():
    """Entry point"""
    console.print()
    inventory = AWSResourceInventory()
    inventory.run()


if __name__ == '__main__':
    main()
