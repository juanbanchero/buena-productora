#!/usr/bin/env python3
"""
BuenaLive Setup Verification Script

Verifies that all dependencies and files are correctly configured before building.
Run this before building the application to catch issues early.

Usage:
    python verify_setup.py
"""

import sys
import os
from pathlib import Path

def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_success(text):
    print(f"[OK] {text}")

def print_warning(text):
    print(f"[WARNING] {text}")

def print_error(text):
    print(f"[ERROR] {text}")

def verify_python_version():
    """Verify Python version is 3.8+"""
    print_header("Python Version")
    version = sys.version_info
    if version >= (3, 8):
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor} found, need 3.8+")
        return False

def verify_required_modules():
    """Verify all required Python modules are installed"""
    print_header("Required Modules")

    required = [
        ('tkinter', 'tkinter'),
        ('selenium', 'selenium'),
        ('gspread', 'gspread'),
        ('google.oauth2', 'google-auth'),
        ('cryptography', 'cryptography'),
        ('tufup', 'tufup'),
        ('PyInstaller', 'pyinstaller'),
        ('bsdiff4', 'bsdiff4'),
        ('packaging', 'packaging'),
    ]

    all_ok = True
    for module_name, package_name in required:
        try:
            __import__(module_name)
            print_success(f"{package_name}")
        except ImportError:
            print_error(f"{package_name} - Install with: pip install {package_name}")
            all_ok = False

    return all_ok

def verify_project_files():
    """Verify required project files exist"""
    print_header("Project Files")

    project_root = Path(__file__).parent
    required_files = [
        'main.py',
        'version.py',
        'updater.py',
        'credential_manager.py',
        'buena-live.spec',
        'requirements.txt',
        'build_scripts/build_mac.py',
        'build_scripts/build_windows.py',
        'build_scripts/publish_update.py',
    ]

    all_ok = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print_success(f"{file_path}")
        else:
            print_error(f"{file_path} - Missing")
            all_ok = False

    # Check credentials.json separately (warning only, not error)
    creds_path = project_root / 'credentials.json'
    if creds_path.exists():
        print_success("credentials.json")
    else:
        print_warning("credentials.json - Not found (needed for Google Sheets)")

    return all_ok

def verify_module_imports():
    """Verify project modules can be imported"""
    print_header("Module Imports")

    all_ok = True
    try:
        from version import __version__
        print_success(f"version.py (v{__version__})")
    except Exception as e:
        print_error(f"version.py - {e}")
        all_ok = False

    try:
        import updater
        print_success("updater.py")
    except Exception as e:
        print_error(f"updater.py - {e}")
        all_ok = False

    try:
        from credential_manager import CredentialManager
        print_success("credential_manager.py")
    except Exception as e:
        print_error(f"credential_manager.py - {e}")
        all_ok = False

    try:
        import main
        print_success("main.py")
    except Exception as e:
        print_error(f"main.py - {e}")
        all_ok = False

    return all_ok

def verify_build_scripts():
    """Verify build scripts are executable and valid"""
    print_header("Build Scripts")

    project_root = Path(__file__).parent
    scripts = [
        'build_scripts/build_mac.py',
        'build_scripts/build_windows.py',
        'build_scripts/publish_update.py',
    ]

    all_ok = True
    for script in scripts:
        script_path = project_root / script
        if script_path.exists():
            # Check if executable
            if os.access(script_path, os.X_OK):
                print_success(f"{script} (executable)")
            else:
                print_warning(f"{script} (not executable - run: chmod +x {script})")
        else:
            print_error(f"{script} - Missing")
            all_ok = False

    return all_ok

def verify_configuration():
    """Verify important configuration settings"""
    print_header("Configuration")

    try:
        from version import __version__
        print_success(f"App version: {__version__}")
    except:
        print_error("Could not read version")

    try:
        import updater
        print_success(f"Update URL: {updater.UPDATE_REPO_URL}")
        if "YOUR_USERNAME" in updater.UPDATE_REPO_URL:
            print_warning("Update URL contains placeholder - update before distribution")
    except:
        print_error("Could not read update configuration")

    return True

def main():
    print("\n" + "*" * 60)
    print("  BuenaLive Setup Verification")
    print("*" * 60)

    all_checks = [
        verify_python_version(),
        verify_required_modules(),
        verify_project_files(),
        verify_module_imports(),
        verify_build_scripts(),
        verify_configuration(),
    ]

    print_header("Summary")

    if all(all_checks):
        print_success("All checks passed!")
        print("\nYou're ready to build the application:")
        print("  macOS:   python build_scripts/build_mac.py --dmg --clean")
        print("  Windows: python build_scripts/build_windows.py --installer --clean")
        return 0
    else:
        print_error("Some checks failed - fix issues before building")
        print("\nCommon fixes:")
        print("  pip install -r requirements.txt")
        print("  chmod +x build_scripts/*.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())
