#!/usr/bin/env python3
"""
BuenaLive Update Publisher Script

Publishes new application versions to the update repository using tufup.
Handles archive creation, patch generation, and metadata signing.

Requirements:
    - tufup installed (pip install tufup)
    - Built application in dist/ directory
    - Initialized tufup repository (run --init-repo first time)

Usage:
    # First time setup
    python build_scripts/publish_update.py --init-repo

    # Publish new version
    python build_scripts/publish_update.py

    # Publish to custom repository
    python build_scripts/publish_update.py --repo-dir /path/to/repo

Options:
    --init-repo: Initialize new tufup repository (first time only)
    --repo-dir PATH: Custom repository directory (default: tufup_repo/)
    --skip-patch: Skip patch generation, only create full archive

Output:
    - tufup_repo/metadata/: TUF metadata files
    - tufup_repo/targets/: Application archives and patches
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from version import __version__
from tufup.repo import Repository
from tufup.common import SUFFIX_ARCHIVE

APP_NAME = "BuenaLive"
DEFAULT_REPO_DIR = project_root / "tufup_repo"

def init_repository(repo_dir: Path):
    """
    Initialize a new tufup repository.

    Args:
        repo_dir: Path to repository directory

    Notes:
        - Creates necessary directory structure
        - Generates cryptographic keys for signing
        - Initializes TUF metadata
    """
    print(f"Initializing tufup repository at {repo_dir}...")

    if repo_dir.exists():
        response = input(f"Repository {repo_dir} already exists. Reinitialize? (y/N): ")
        if response.lower() != 'y':
            print("Aborted")
            return False

        # Backup existing repo
        backup_dir = repo_dir.parent / f"{repo_dir.name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"Backing up existing repository to {backup_dir}")
        shutil.copytree(repo_dir, backup_dir)
        shutil.rmtree(repo_dir)

    # Create repository
    try:
        repo = Repository(
            app_name=APP_NAME,
            app_version_attr="version",
            repo_dir=repo_dir
        )

        # Initialize metadata
        repo.initialize()

        print("\n✓ Repository initialized successfully")
        print(f"\nRepository structure:")
        print(f"  {repo_dir}/")
        print(f"  ├── metadata/     # TUF metadata files")
        print(f"  └── targets/      # Application archives and patches")
        print("\nNext steps:")
        print("  1. Build your application (build_mac.py or build_windows.py)")
        print("  2. Publish the build: python build_scripts/publish_update.py")

        return True

    except Exception as e:
        print(f"ERROR: Failed to initialize repository: {e}")
        return False

def find_dist_bundle() -> Path:
    """
    Find the built application bundle in dist/ directory.

    Returns:
        Path: Path to application bundle (.app for Mac, directory for Windows)

    Raises:
        FileNotFoundError: If no bundle found
    """
    dist_dir = project_root / "dist"

    if not dist_dir.exists():
        raise FileNotFoundError(
            f"dist/ directory not found. Build the application first:\n"
            f"  Mac: python build_scripts/build_mac.py\n"
            f"  Windows: python build_scripts/build_windows.py"
        )

    # Look for .app (Mac) or BuenaLive directory (Windows)
    candidates = []

    # Mac .app bundle
    app_bundle = dist_dir / f"{APP_NAME}.app"
    if app_bundle.exists() and app_bundle.is_dir():
        candidates.append(app_bundle)

    # Windows executable (single file)
    exe_file = dist_dir / f"{APP_NAME}.exe"
    if exe_file.exists():
        candidates.append(exe_file)

    # Windows directory bundle (if using --onedir)
    win_dir = dist_dir / APP_NAME
    if win_dir.exists() and win_dir.is_dir():
        candidates.append(win_dir)

    if not candidates:
        raise FileNotFoundError(
            f"No built application found in {dist_dir}/\n"
            f"Expected: {APP_NAME}.app (Mac) or {APP_NAME}.exe (Windows)"
        )

    # Prefer most recently modified
    latest = max(candidates, key=lambda p: p.stat().st_mtime)
    return latest

def create_archive(bundle_path: Path, output_dir: Path) -> Path:
    """
    Create a tufup archive from application bundle.

    Args:
        bundle_path: Path to application bundle
        output_dir: Directory to store archive

    Returns:
        Path: Path to created archive

    Notes:
        Archive format: {app_name}-{version}.tar.gz
    """
    print(f"\nCreating archive from {bundle_path}...")

    archive_name = f"{APP_NAME}-{__version__}{SUFFIX_ARCHIVE}"
    archive_path = output_dir / archive_name

    # Create archive using tufup's method
    # For now, use tar command (tufup will handle this internally)
    import tarfile

    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(bundle_path, arcname=bundle_path.name)

    print(f"✓ Created archive: {archive_path}")
    print(f"  Size: {archive_path.stat().st_size / (1024*1024):.2f} MB")

    return archive_path

def publish_version(repo_dir: Path, skip_patch: bool = False):
    """
    Publish new version to update repository.

    Args:
        repo_dir: Path to repository directory
        skip_patch: If True, only create full archive (no patches)

    Notes:
        - Finds built application in dist/
        - Creates archive and patches
        - Updates TUF metadata
        - Signs metadata with private keys
    """
    print(f"\nPublishing BuenaLive v{__version__}...")

    # Verify repository exists
    if not repo_dir.exists():
        print(f"ERROR: Repository not found at {repo_dir}")
        print("Initialize repository first: --init-repo")
        return False

    # Find built bundle
    try:
        bundle_path = find_dist_bundle()
        print(f"Found bundle: {bundle_path}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return False

    # Initialize repository object
    try:
        repo = Repository(
            app_name=APP_NAME,
            app_version_attr="version",
            repo_dir=repo_dir
        )
    except Exception as e:
        print(f"ERROR: Failed to load repository: {e}")
        return False

    # Create archive
    targets_dir = repo_dir / "targets"
    targets_dir.mkdir(exist_ok=True)

    try:
        archive_path = create_archive(bundle_path, targets_dir)
    except Exception as e:
        print(f"ERROR: Failed to create archive: {e}")
        return False

    # Add to repository
    try:
        print(f"\nAdding version {__version__} to repository...")

        # This will:
        # 1. Add archive to targets
        # 2. Generate patch from previous version (if exists and not skip_patch)
        # 3. Update and sign metadata
        repo.add_bundle(
            new_bundle_path=archive_path,
            new_version=__version__,
            skip_patch=skip_patch
        )

        print(f"✓ Version {__version__} published successfully")

        # Show repository status
        print(f"\nRepository: {repo_dir}")
        print(f"  Metadata: {repo_dir}/metadata/")
        print(f"  Targets: {repo_dir}/targets/")

        # List target files
        target_files = list(targets_dir.glob("*"))
        print(f"\n  Available versions:")
        for target_file in sorted(target_files):
            if target_file.is_file():
                size_mb = target_file.stat().st_size / (1024*1024)
                print(f"    - {target_file.name} ({size_mb:.2f} MB)")

        print("\nNext steps:")
        print("  1. Test the update locally")
        print("  2. Upload repository to server/GitHub:")
        print(f"     - Upload {repo_dir}/metadata/ to your update server")
        print(f"     - Upload {repo_dir}/targets/ to your update server")
        print("  3. Update UPDATE_REPO_URL in updater.py to point to your server")
        print("\n  For GitHub Releases:")
        print("     - Create new release with tag v{__version__}")
        print("     - Upload metadata/ and targets/ directories")

        return True

    except Exception as e:
        print(f"ERROR: Failed to publish version: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description="Publish BuenaLive update")
    parser.add_argument(
        "--init-repo",
        action="store_true",
        help="Initialize new tufup repository (first time only)"
    )
    parser.add_argument(
        "--repo-dir",
        type=Path,
        default=DEFAULT_REPO_DIR,
        help=f"Repository directory (default: {DEFAULT_REPO_DIR})"
    )
    parser.add_argument(
        "--skip-patch",
        action="store_true",
        help="Skip patch generation, only create full archive"
    )
    args = parser.parse_args()

    print("=" * 70)
    print(f"BuenaLive Update Publisher v{__version__}")
    print("=" * 70)

    # Initialize repository if requested
    if args.init_repo:
        return 0 if init_repository(args.repo_dir) else 1

    # Publish version
    return 0 if publish_version(args.repo_dir, args.skip_patch) else 1

if __name__ == "__main__":
    sys.exit(main())
