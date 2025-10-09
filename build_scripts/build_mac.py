#!/usr/bin/env python3
"""
BuenaLive Mac Build Script

Builds the BuenaLive application for macOS using PyInstaller.
Creates a .app bundle and optionally a .dmg installer.

Requirements:
    - PyInstaller installed (pip install pyinstaller)
    - macOS system (for .app bundle creation)
    - Optional: create-dmg for .dmg creation (brew install create-dmg)

Usage:
    python build_scripts/build_mac.py [--dmg] [--clean]

Options:
    --dmg: Create .dmg installer after building .app
    --clean: Clean build directories before building

Output:
    - dist/TicketeraBuena.app: macOS application bundle
    - dist/TicketeraBuena.dmg: macOS installer (if --dmg specified)
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from version import __version__

def clean_build_dirs():
    """Remove build and dist directories."""
    print("Cleaning build directories...")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        dir_path = project_root / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed {dir_name}/")

def build_app():
    """Build the macOS .app bundle using PyInstaller."""
    print(f"\nBuilding Ticketera Buena v{__version__} for macOS...")

    # Check if spec file exists
    spec_file = project_root / "buena-live.spec"
    if not spec_file.exists():
        print(f"ERROR: Spec file not found: {spec_file}")
        return False

    # Run PyInstaller
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)

    if result.returncode != 0:
        print("ERROR: PyInstaller build failed")
        return False

    # Check if .app was created
    app_path = project_root / "dist" / "TicketeraBuena.app"
    if not app_path.exists():
        print(f"ERROR: App bundle not found at {app_path}")
        return False

    print(f"\n✓ Successfully built: {app_path}")
    print(f"  Size: {get_dir_size(app_path):.2f} MB")
    return True

def create_dmg():
    """Create a .dmg installer from the .app bundle."""
    print("\nCreating .dmg installer...")

    # Check if create-dmg is installed
    if shutil.which("create-dmg") is None:
        print("WARNING: create-dmg not found. Install with: brew install create-dmg")
        print("Skipping .dmg creation")
        return False

    app_path = project_root / "dist" / "TicketeraBuena.app"
    dmg_path = project_root / "dist" / f"TicketeraBuena-{__version__}-mac.dmg"

    # Remove existing DMG if it exists
    if dmg_path.exists():
        dmg_path.unlink()

    # Create DMG
    cmd = [
        "create-dmg",
        "--volname", f"Ticketera Buena {__version__}",
        "--window-pos", "200", "120",
        "--window-size", "800", "400",
        "--icon-size", "100",
        "--app-drop-link", "600", "185",
        str(dmg_path),
        str(app_path)
    ]

    print(f"Running: create-dmg...")
    result = subprocess.run(cmd, cwd=project_root, capture_output=True)

    # Note: create-dmg sometimes returns non-zero even on success
    if dmg_path.exists():
        print(f"\n✓ Successfully created: {dmg_path}")
        print(f"  Size: {dmg_path.stat().st_size / (1024*1024):.2f} MB")
        return True
    else:
        print("ERROR: DMG creation failed")
        return False

def get_dir_size(path):
    """Calculate total size of directory in MB."""
    total = 0
    for entry in Path(path).rglob('*'):
        if entry.is_file():
            total += entry.stat().st_size
    return total / (1024 * 1024)

def verify_dependencies():
    """Verify all required dependencies are present."""
    print("Verifying dependencies...")

    # Check credentials.json
    credentials_path = project_root / "credentials.json"
    if not credentials_path.exists():
        print(f"WARNING: credentials.json not found at {credentials_path}")
        print("  The built app will not be able to access Google Sheets")

    # Check if we're in virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("WARNING: Not running in virtual environment")
        print("  Consider activating venv: source venv/bin/activate")

    print("✓ Dependency check complete\n")

def main():
    parser = argparse.ArgumentParser(description="Build BuenaLive for macOS")
    parser.add_argument("--dmg", action="store_true", help="Create .dmg installer")
    parser.add_argument("--clean", action="store_true", help="Clean build directories first")
    args = parser.parse_args()

    print("=" * 60)
    print(f"Ticketera Buena - Mac Build Script v{__version__}")
    print("=" * 60)

    # Verify we're on macOS
    if sys.platform != "darwin":
        print("ERROR: This script must be run on macOS")
        return 1

    # Verify dependencies
    verify_dependencies()

    # Clean if requested
    if args.clean:
        clean_build_dirs()

    # Build the app
    if not build_app():
        return 1

    # Create DMG if requested
    if args.dmg:
        create_dmg()

    print("\n" + "=" * 60)
    print("Build complete!")
    print("=" * 60)
    print(f"\nOutput:")
    print(f"  App: dist/TicketeraBuena.app")
    if args.dmg:
        print(f"  Installer: dist/TicketeraBuena-{__version__}-mac.dmg")
    print("\nNext steps:")
    print("  1. Test the application: open dist/TicketeraBuena.app")
    print("  2. Distribute the .dmg file (if created)")
    print("  3. Publish update using: python build_scripts/publish_update.py")

    return 0

if __name__ == "__main__":
    sys.exit(main())
