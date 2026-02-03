# Contributing to AWS Resource Inventory

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/aws-resource-inventory.git
   cd aws-resource-inventory
   ```

2. **Install uv (if not already installed):**
   ```bash
   pip install uv
   ```

3. **Set up the development environment:**
   ```bash
   uv sync
   uv run pre-commit install
   ```

## Code Quality Standards

This project maintains high code quality standards using modern Python tooling:

### Formatting and Linting
- **Ruff** handles both formatting and linting
- Line length: 100 characters
- Follow PEP 8 style guidelines

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check . --fix
```

### Type Checking
- Use type hints for all function signatures
- Run Pyright before committing

```bash
uv run pyright
```

### Testing
- Write tests for new features
- Maintain or improve code coverage
- Use pytest fixtures for common setup

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov
```

## Pre-commit Hooks

Pre-commit hooks automatically run before each commit:
- Trailing whitespace removal
- File formatting
- YAML/JSON/TOML validation
- Secret detection
- Ruff linting and formatting
- Markdown formatting

```bash
# Run manually
uv run pre-commit run --all-files
```

## Pull Request Process

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clean, documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Run quality checks:**
   ```bash
   uv run ruff format .
   uv run ruff check . --fix
   uv run pyright
   uv run pytest
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```
   
   Use [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `test:` - Test additions/changes
   - `refactor:` - Code refactoring
   - `chore:` - Maintenance tasks

5. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   ```
   
   Then open a Pull Request on GitHub.

## Adding New Resource Scanners

To add support for a new AWS resource type:

1. **Create a new scanner module** in `src/aws_resource_inventory/scanners/`:
   ```python
   from .base import BaseScanner
   
   class NewServiceScanner(BaseScanner):
       sheet_name = "Service Name"
       is_global = False  # or True for global services
       
       def scan_account_region(self, credentials, account_id, account_name, region):
           # Implementation
           pass
   ```

2. **Register the scanner** in `src/aws_resource_inventory/scanners/__init__.py`

3. **Write tests** in `tests/test_scanners.py`

4. **Update documentation** in README.md

## Code Review Guidelines

Reviewers will check for:
- Code quality and readability
- Test coverage
- Documentation updates
- Type hints
- Security considerations
- Performance implications

## Questions or Issues?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
