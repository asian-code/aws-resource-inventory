# Makefile for AWS Resource Inventory

.PHONY: help install dev test lint format typecheck clean run pre-commit

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync

dev: ## Install with dev dependencies
	uv sync --all-extras

test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage
	uv run pytest --cov --cov-report=html --cov-report=term

lint: ## Run linter
	uv run ruff check .

lint-fix: ## Run linter with auto-fix
	uv run ruff check . --fix

format: ## Format code
	uv run ruff format .

format-check: ## Check code formatting
	uv run ruff format --check .

typecheck: ## Run type checker
	uv run pyright

quality: format lint typecheck ## Run all quality checks

pre-commit: ## Run pre-commit hooks
	uv run pre-commit run --all-files

pre-commit-install: ## Install pre-commit hooks
	uv run pre-commit install

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/
	rm -f .coverage
	rm -f coverage.xml

run: ## Run the inventory scanner
	uv run aws-inventory

build: ## Build the package
	uv build

upgrade: ## Upgrade all dependencies
	uv sync --upgrade
