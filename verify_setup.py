"""
Post-Modernization Verification Script
Run this to verify the project setup is correct.
"""

import sys
from pathlib import Path


def check_file(path: Path, description: str) -> bool:
    """Check if a file exists."""
    exists = path.exists()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path.name}")
    return exists


def check_directory(path: Path, description: str) -> bool:
    """Check if a directory exists."""
    exists = path.is_dir()
    status = "✅" if exists else "❌"
    print(f"{status} {description}: {path.name}/")
    return exists


def main():
    """Run verification checks."""
    root = Path(__file__).parent
    all_good = True

    print("\n🔍 Verifying Project Structure\n")
    print("=" * 60)

    # Core configuration files
    print("\n📋 Configuration Files:")
    all_good &= check_file(root / "pyproject.toml", "Project config")
    all_good &= check_file(root / ".gitignore", "Git ignore")
    all_good &= check_file(root / ".editorconfig", "Editor config")
    all_good &= check_file(root / ".pre-commit-config.yaml", "Pre-commit hooks")

    # Documentation
    print("\n📚 Documentation:")
    all_good &= check_file(root / "README.md", "README")
    all_good &= check_file(root / "CONTRIBUTING.md", "Contributing guide")
    all_good &= check_file(root / "CHANGELOG.md", "Changelog")
    all_good &= check_file(root / "LICENSE", "License")
    all_good &= check_file(root / "QUICKSTART.md", "Quick start guide")

    # Source code
    print("\n🐍 Source Code:")
    all_good &= check_directory(root / "src", "Source directory")
    all_good &= check_directory(root / "src" / "aws_resource_inventory", "Main package")
    all_good &= check_file(
        root / "src" / "aws_resource_inventory" / "__init__.py",
        "Package init"
    )
    all_good &= check_file(
        root / "src" / "aws_resource_inventory" / "main.py",
        "Main module"
    )
    all_good &= check_file(
        root / "src" / "aws_resource_inventory" / "config.py",
        "Config module"
    )
    all_good &= check_directory(
        root / "src" / "aws_resource_inventory" / "scanners",
        "Scanners package"
    )

    # Tests
    print("\n🧪 Tests:")
    all_good &= check_directory(root / "tests", "Tests directory")
    all_good &= check_file(root / "tests" / "conftest.py", "Test fixtures")
    all_good &= check_file(root / "tests" / "test_config.py", "Config tests")

    # CI/CD
    print("\n🔄 CI/CD:")
    all_good &= check_directory(root / ".github", "GitHub directory")
    all_good &= check_directory(root / ".github" / "workflows", "Workflows directory")
    all_good &= check_file(
        root / ".github" / "workflows" / "ci.yml",
        "CI workflow"
    )
    all_good &= check_file(
        root / ".github" / "dependabot.yml",
        "Dependabot config"
    )

    # Project files
    print("\n📦 Project Files:")
    all_good &= check_file(root / "inventory-config.json.example", "Config example")
    all_good &= check_directory(root / "output", "Output directory")

    # Summary
    print("\n" + "=" * 60)
    if all_good:
        print("\n✅ All checks passed! Project structure is correct.")
        print("\n📝 Next steps:")
        print("   1. Run: uv sync")
        print("   2. Run: uv run pytest")
        print("   3. Run: uv run aws-inventory")
        return 0
    else:
        print("\n❌ Some checks failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
