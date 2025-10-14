#!/usr/bin/env python3
"""
Update version.py from git tag or environment variable.

This script is used during CI/CD to automatically set the version
from the git tag (e.g., v1.2.3 -> 1.2.3).

Usage:
    # From git tag
    python build_scripts/update_version.py

    # From environment variable (CI/CD)
    export VERSION_TAG=v1.2.3
    python build_scripts/update_version.py

    # Manual version
    python build_scripts/update_version.py --version 1.2.3
"""

import os
import sys
import re
import subprocess
import argparse
from pathlib import Path

project_root = Path(__file__).parent.parent
version_file = project_root / "version.py"


def get_version_from_git():
    """Get version from git tag."""
    try:
        # Get the current tag
        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            capture_output=True,
            text=True,
            check=True,
            cwd=project_root
        )
        tag = result.stdout.strip()
        print(f"Found git tag: {tag}")
        return tag
    except subprocess.CalledProcessError:
        print("WARNING: No git tag found on current commit")
        return None


def get_version_from_env():
    """Get version from environment variable."""
    # GitHub Actions sets GITHUB_REF for tags as 'refs/tags/v1.2.3'
    github_ref = os.environ.get('GITHUB_REF', '')
    if github_ref.startswith('refs/tags/'):
        tag = github_ref.replace('refs/tags/', '')
        print(f"Found version from GITHUB_REF: {tag}")
        return tag

    # Also check VERSION_TAG environment variable
    version_tag = os.environ.get('VERSION_TAG', '')
    if version_tag:
        print(f"Found version from VERSION_TAG: {version_tag}")
        return version_tag

    return None


def parse_version(version_string):
    """
    Parse version string and extract semantic version.

    Supports:
        - v1.2.3 -> 1.2.3
        - 1.2.3 -> 1.2.3
        - v1.2.3-beta -> 1.2.3-beta
    """
    if not version_string:
        return None

    # Remove leading 'v' if present
    version_string = version_string.strip()
    if version_string.startswith('v'):
        version_string = version_string[1:]

    # Validate semantic versioning format
    semver_pattern = r'^\d+\.\d+\.\d+(-[\w\.]+)?$'
    if not re.match(semver_pattern, version_string):
        print(f"ERROR: Invalid version format: {version_string}")
        print("Expected format: MAJOR.MINOR.PATCH (e.g., 1.2.3)")
        return None

    return version_string


def read_current_version():
    """Read current version from version.py."""
    if not version_file.exists():
        return None

    with open(version_file, 'r') as f:
        content = f.read()

    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)
    return None


def update_version_file(new_version):
    """Update version.py with new version."""
    if not version_file.exists():
        print(f"ERROR: version.py not found at {version_file}")
        return False

    # Read current file
    with open(version_file, 'r') as f:
        content = f.read()

    # Replace version string
    new_content = re.sub(
        r'__version__\s*=\s*["\'][^"\']+["\']',
        f'__version__ = "{new_version}"',
        content
    )

    # Write back
    with open(version_file, 'w') as f:
        f.write(new_content)

    print(f"✓ Updated version.py: {new_version}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Update version.py from git tag")
    parser.add_argument(
        "--version",
        help="Manually specify version (e.g., 1.2.3)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Version Update Script")
    print("=" * 60)

    # Get current version
    current_version = read_current_version()
    print(f"Current version: {current_version or 'NOT FOUND'}")

    # Determine new version
    new_version_raw = None

    if args.version:
        # Manual version specified
        new_version_raw = args.version
        print(f"Using manual version: {new_version_raw}")
    else:
        # Try environment variable first (for CI/CD)
        new_version_raw = get_version_from_env()

        # Fall back to git tag
        if not new_version_raw:
            new_version_raw = get_version_from_git()

    if not new_version_raw:
        print("\nERROR: No version found!")
        print("Options:")
        print("  1. Create a git tag: git tag v1.2.3")
        print("  2. Set environment variable: export VERSION_TAG=v1.2.3")
        print("  3. Specify manually: --version 1.2.3")
        return 1

    # Parse version
    new_version = parse_version(new_version_raw)
    if not new_version:
        return 1

    print(f"Parsed version: {new_version}")

    # Check if version changed
    if current_version == new_version:
        print(f"\n✓ Version already up to date: {new_version}")
        return 0

    # Update version file
    if args.dry_run:
        print(f"\n[DRY RUN] Would update version.py: {current_version} -> {new_version}")
        return 0

    if not update_version_file(new_version):
        return 1

    print("\n" + "=" * 60)
    print(f"Version updated: {current_version} -> {new_version}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
