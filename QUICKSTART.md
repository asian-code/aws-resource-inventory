# Quick Reference Guide

## Installation

```bash
# Install uv
pip install uv

# Setup project
uv sync
```

## Running the Tool

```bash
# Using uv (recommended)
uv run aws-inventory

# Alternative methods
python -m aws_resource_inventory.main
python src/aws_resource_inventory/main.py
```

## Development Commands

```bash
# Code formatting
uv run ruff format .

# Linting (with auto-fix)
uv run ruff check . --fix

# Type checking
uv run pyright

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Pre-commit hooks
uv run pre-commit run --all-files
```

## Adding Dependencies

```bash
# Runtime dependency
uv add package-name

# Development dependency
uv add --dev package-name
```

## Makefile Commands

```bash
make help          # Show all commands
make install       # Install dependencies
make test          # Run tests
make lint          # Run linter
make format        # Format code
make quality       # Run all checks
make run           # Run the scanner
```

## Configuration File

Edit `sso-config.json`:

```json
{
  "sso_start_url": "https://your-sso.awsapps.com/start",
  "sso_region": "us-east-1",
  "role_name": "YourRoleName",
  "target_regions": ["us-east-1", "us-west-2"],
  "max_workers": 20,
  "account_blacklist": []
}
```

## Project Structure

```
src/aws_resource_inventory/   # Main package
├── main.py                    # Entry point
├── config.py                  # Configuration
├── aws_auth.py               # SSO authentication
├── excel_exporter.py         # Excel output
└── scanners/                 # Resource scanners

tests/                        # Test suite
.github/workflows/           # CI/CD
```

## Common Issues

**Import errors after restructuring:**
- Make sure you're running commands with `uv run`
- Or activate the venv: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Linux/Mac)

**Pre-commit hooks failing:**
- Run `uv run ruff format .` first
- Then `uv run ruff check . --fix`
- Finally retry commit

**Type checking errors:**
- Install type stubs: `uv add --dev boto3-stubs[essential]`
- Some errors can be ignored with `# type: ignore` comments

## CI/CD Pipeline

GitHub Actions automatically runs on push/PR:
- Code quality checks (Ruff, Pyright)
- Security scanning (Gitleaks, Bandit)
- Tests on Python 3.11, 3.12, 3.13
- Dependency review
- Build verification

## Resources

- [uv documentation](https://docs.astral.sh/uv/)
- [Ruff rules](https://docs.astral.sh/ruff/rules/)
- [Pyright configuration](https://microsoft.github.io/pyright/)
- [pytest documentation](https://docs.pytest.org/)
