# AWS Resource Inventory Tool

A comprehensive Python tool to scan **all AWS resources** across an entire AWS Organization and export the inventory to individual Excel files per resource type.

## Features

- 🔐 **AWS OIDC Authentication** - Secure authentication using GitHub Actions OIDC or environment credentials
- 🏢 **Organization-wide Scanning** - Scans all accounts in your AWS Organization via cross-account role assumption
- 🌍 **Multi-Region Support** - Configurable target regions (default: us-east-1, us-west-2)
- ⚡ **Parallel Processing** - Multi-threaded scanning for speed and efficiency (20 workers)
- 📊 **Individual Excel Files** - One Excel file per resource type (PascalCase naming)
- 📈 **Summary File** - Overview of all resources found with counts
- ❌ **Errors Sheet** - Tracks any skipped accounts or failures
- 🛡️ **Account Blacklist** - Exclude specific accounts from scanning
- ☁️ **S3 Upload** - Automatic upload to S3 bucket (CI/CD)
- 🎨 **Rich CLI Output** - Beautiful progress bars and summary statistics
- 🔄 **Scheduled Scans** - GitHub Actions workflow runs monthly (1st of each month)

## Supported Resource Types (37 total)

### Compute
- EC2 Instances
- Lambda Functions
- ECS Services
- ECS Tasks
- EKS Clusters
- Auto Scaling Groups

### Storage
- S3 Buckets (Global)
- EBS Volumes
- EFS File Systems

### Database
- RDS Instances
- DynamoDB Tables
- ElastiCache Clusters
- Redshift Clusters

### Networking
- VPCs
- Subnets
- Route Tables
- Security Groups
- NAT Gateways
- Internet Gateways
- Elastic IPs
- Transit Gateway Attachments

### Load Balancing
- Application/Network Load Balancers
- Target Groups

### Identity (Global)
- IAM Users
- IAM Roles
- IAM Policies (Customer Managed)

### Security
- KMS Keys
- Secrets Manager Secrets
- ACM Certificates

### CloudFormation
- CloudFormation Stacks
- CloudFormation StackSets (Global)

### Other
- CloudWatch Alarms
- SNS Topics
- SQS Queues
- API Gateway (REST & HTTP APIs)
- CloudFront Distributions (Global)

## Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip
- AWS credentials with Organizations read access and ability to assume cross-account roles
- Cross-account role (e.g., `AWSControlTowerExecution`) in each target account

## Installation

### Quick Start with uv (Recommended)

1. **Install uv:**
   ```bash
   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Linux/Mac
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Clone and setup:**
   ```bash
   git clone https://github.com/asian-code/aws-resource-inventory.git
   cd aws-resource-inventory
   uv sync
   ```

### Traditional Installation with pip

1. **Clone the repository:**
   ```bash
   git clone https://github.com/asian-code/aws-resource-inventory.git
   cd aws-resource-inventory
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   ```

## Configuration

Edit `inventory-config.json` to match your environment:

```json
{
  "cross_account_role_name": "AWSControlTowerExecution",
  "target_regions": ["us-east-1", "us-west-2"],
  "max_workers": 20,
  "account_blacklist": [],
  "output_dir": "output",
  "s3_bucket": null,
  "s3_prefix": ""
}
```

### Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `cross_account_role_name` | IAM role to assume in each account | `AWSControlTowerExecution` |
| `target_regions` | List of AWS regions to scan | `["us-east-1", "us-west-2"]` |
| `max_workers` | Number of parallel threads | `20` |
| `output_dir` | Directory for output files | `"output"` |
| `account_blacklist` | Account IDs to exclude from scanning | `[]` |
| `s3_bucket` | S3 bucket for uploading results | `null` |
| `s3_prefix` | Prefix/folder in S3 bucket | `""` |

### Account Blacklist Example

To exclude specific accounts from scanning:

```json
{
  "account_blacklist": [
    "123456789012",
    "987654321098"
  ]
}
```

## Usage

### Running Locally

With uv (recommended):
```bash
# Set AWS credentials in environment first
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...

uv run aws-inventory
```

Or directly with Python:
```bash
python -m aws_resource_inventory.main
```

### GitHub Actions (Automated Monthly Scan)

The included workflow (`.github/workflows/inventory-scan.yml`) runs automatically on the 1st of each month and uploads results to S3.

**Setup:**
1. Configure GitHub repository secret: `AWS_OIDC_ROLE_ARN`
2. Ensure the OIDC role has permissions to:
   - Read AWS Organizations
   - Assume the cross-account role in all accounts
   - Write to the S3 bucket

**Manual Trigger:**
- Go to Actions → "AWS Resource Inventory Scan" → "Run workflow"
- Optionally disable S3 upload for testing

### What Happens

1. **Credential Verification** - Validates AWS credentials
2. **Account Discovery** - Fetches all accounts from AWS Organizations
3. **Blacklist Filtering** - Excludes any accounts in the blacklist
4. **Parallel Scanning** - Scans all 37 resource types across all accounts and regions
5. **Excel Export** - Creates individual Excel files per resource type
6. **S3 Upload** - Uploads files to configured S3 bucket (if enabled)
7. **Summary Report** - Displays statistics and any errors

## Output

### Excel Files Structure

Individual files are created per resource type (PascalCase naming):

```
output/
├── Ec2Instances.xlsx
├── LambdaFunctions.xlsx
├── S3Buckets.xlsx
├── CloudFormationStacks.xlsx
├── CloudFormationStackSets.xlsx
├── ...
└── Summary.xlsx
```

The **Summary.xlsx** file contains:
- Scan timestamp
- Number of accounts scanned
- Number of regions scanned
- Total resource count
- Count per resource type
- Errors/skipped accounts sheet

2. **Resource Sheets** - One sheet per resource type (only created if resources exist):
   - Formatted headers with auto-filter
   - Auto-sized columns
   - Frozen header row
   - All standard fields including tags

3. **Errors-Skipped Sheet** - Lists any:
   - Failed account credentials
   - Access denied errors
   - Timeout or other issues

### Standard Fields per Resource

Most resources include these standard fields:
- Resource Name/ID
- Account ID & Account Name
- Region (or "global" for global resources)
- ARN
- State/Status
- Created Date
- Tags (formatted as `Key=Value; Key2=Value2`)

Plus resource-specific fields (e.g., Instance Type for EC2, Engine for RDS).

## Required IAM Permissions

The IAM role needs read-only access to all scanned services. Example policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "lambda:List*",
        "lambda:GetFunction",
        "ecs:List*",
        "ecs:Describe*",
        "eks:List*",
        "eks:Describe*",
        "autoscaling:Describe*",
        "s3:ListAllMyBuckets",
        "s3:GetBucket*",
        "elasticfilesystem:Describe*",
        "rds:Describe*",
        "rds:ListTagsForResource",
        "dynamodb:List*",
        "dynamodb:Describe*",
        "elasticache:Describe*",
        "elasticache:ListTagsForResource",
        "redshift:Describe*",
        "elasticloadbalancing:Describe*",
        "iam:List*",
        "iam:Get*",
        "kms:List*",
        "kms:Describe*",
        "kms:GetKeyRotationStatus",
        "secretsmanager:List*",
        "acm:List*",
        "acm:Describe*",
        "cloudwatch:Describe*",
        "cloudwatch:ListTagsForResource",
        "sns:List*",
        "sns:GetTopicAttributes",
        "sqs:List*",
        "sqs:GetQueueAttributes",
        "apigateway:GET",
        "cloudfront:List*",
        "cloudfront:GetDistribution",
        "tag:GetResources"
      ],
      "Resource": "*"
    }
  ]
}
```

## Project Structure

```
aws-resource-inventory/
├── .github/
│   ├── workflows/             # CI/CD pipelines
│   │   ├── ci.yml            # Main CI workflow
│   │   └── dependabot-auto-merge.yml
│   └── dependabot.yml        # Dependency updates
├── src/
│   └── aws_resource_inventory/  # Main package (src layout)
│       ├── __init__.py
│       ├── main.py            # Main orchestrator
│       ├── aws_auth.py        # AWS SSO authentication
│       ├── config.py          # Configuration loader
│       ├── excel_exporter.py  # Multi-sheet Excel export
│       └── scanners/          # Resource scanner modules
│           ├── __init__.py
│           ├── base.py        # Base scanner class
│           ├── ec2.py         # EC2 instances
│           ├── lambda_functions.py
│           ├── ecs.py, eks.py, autoscaling.py
│           ├── s3.py, ebs.py, efs.py
│           ├── rds.py, dynamodb.py, elasticache.py, redshift.py
│           ├── vpc.py, security_groups.py, nat_igw.py, eip.py, tgw.py
│           ├── elb.py, iam.py, kms.py, secrets.py, acm.py
│           └── cloudwatch.py, sns.py, sqs.py, apigateway.py, cloudfront.py
├── tests/                     # Test suite
│   ├── conftest.py           # Test fixtures
│   ├── test_config.py        # Config tests
│   ├── test_scanners.py      # Scanner tests
│   └── test_integration.py   # Integration tests
├── output/                    # Generated Excel files
├── .editorconfig             # Editor configuration
├── .gitignore                # Git ignore rules
├── .pre-commit-config.yaml   # Pre-commit hooks
├── pyproject.toml            # Project config (replaces requirements.txt)
├── inventory-config.json     # AWS authentication configuration
├── uv.lock                   # Dependency lockfile
└── README.md
```

## Development

### Setting Up Development Environment

```bash
# Install uv if not already installed
pip install uv

# Clone and setup
git clone https://github.com/asian-code/aws-resource-inventory.git
cd aws-resource-inventory

# Create environment and install dependencies (including dev dependencies)
uv sync

# Install pre-commit hooks
uv run pre-commit install
```

### Code Quality Tools

This project uses modern Python tooling:

- **uv** - Fast package manager and environment management
- **Ruff** - Lightning-fast linting and formatting (replaces Black, isort, flake8)
- **Pyright** - Static type checking
- **pytest** - Testing framework with coverage
- **pre-commit** - Automated code quality checks before commits

### Running Quality Checks

```bash
# Format code
uv run ruff format .

# Lint code (with auto-fix)
uv run ruff check . --fix

# Type check
uv run pyright

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

### Adding New Dependencies

```bash
# Add runtime dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Update all dependencies
uv sync --upgrade
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_config.py

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov --cov-report=html
```

## CI/CD

The project includes GitHub Actions workflows for:
- **Code quality checks** (Ruff, Pyright)
- **Security scanning** (Gitleaks, Bandit)
- **Testing** (pytest on Python 3.11, 3.12, 3.13)
- **Dependency review** (on PRs)
- **Automated Dependabot** updates

## Performance Notes

- **200 accounts** with 20 workers typically completes in 15-30 minutes
- Global resources (IAM, S3, CloudFront) are scanned once per account
- Empty resource sheets are skipped to keep the Excel file clean
- Progress is shown in real-time with estimated completion time

## Troubleshooting

### Access Denied Errors
- Ensure your SSO role has the required permissions
- Check if the account is in AWS Organizations
- Verify the role name matches across all accounts

### Slow Performance
- Reduce `max_workers` if you're hitting API rate limits
- Consider scanning fewer regions or resource types

### Memory Issues
- For very large organizations, consider running in batches
- Use the account blacklist to exclude non-essential accounts

## License

MIT License

