#!/usr/bin/env python3
"""
TicketeraBuena Windows Build Script

Builds the TicketeraBuena application for Windows using PyInstaller.
Creates an executable and optionally an NSIS installer.

Requirements:
    - PyInstaller installed (pip install pyinstaller)
    - Windows system (for .exe creation)
    - Optional: NSIS for installer creation (https://nsis.sourceforge.io/)

Usage:
    python build_scripts/build_windows.py [--installer] [--clean]

Options:
    --installer: Create NSIS installer after building .exe
    --clean: Clean build directories before building

Output:
    - dist/TicketeraBuena.exe: Windows executable
    - dist/TicketeraBuena-Setup.exe: Windows installer (if --installer specified)
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

def build_exe():
    """Build the Windows executable using PyInstaller."""
    print(f"\nBuilding TicketeraBuena v{__version__} for Windows...")

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

    # Check if .exe was created
    exe_path = project_root / "dist" / "TicketeraBuena.exe"
    if not exe_path.exists():
        print(f"ERROR: Executable not found at {exe_path}")
        return False

    print(f"\n✓ Successfully built: {exe_path}")
    print(f"  Size: {exe_path.stat().st_size / (1024*1024):.2f} MB")
    return True

def create_nsis_script():
    """Create NSIS installer script."""
    nsis_script = f"""
; TicketeraBuena NSIS Installer Script
; Generated automatically by build_windows.py

!define APP_NAME "TicketeraBuena"
!define APP_VERSION "{__version__}"
!define APP_PUBLISHER "TicketeraBuena"
!define APP_EXE "TicketeraBuena.exe"

; Modern UI
!include "MUI2.nsh"

; General configuration
Name "${{APP_NAME}} ${{APP_VERSION}}"
OutFile "TicketeraBuena-Setup-${{APP_VERSION}}.exe"
InstallDir "$PROGRAMFILES\\${{APP_NAME}}"
InstallDirRegKey HKLM "Software\\${{APP_NAME}}" "Install_Dir"
RequestExecutionLevel admin

; Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${{NSISDIR}}\\Contrib\\Graphics\\Icons\\modern-install.ico"
!define MUI_UNICON "${{NSISDIR}}\\Contrib\\Graphics\\Icons\\modern-uninstall.ico"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Installer Section
Section "Install"
    SetOutPath "$INSTDIR"

    ; Add files
    File /r "dist\\${{APP_EXE}}"

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\\Uninstall.exe"

    ; Registry keys
    WriteRegStr HKLM "Software\\${{APP_NAME}}" "Install_Dir" "$INSTDIR"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "DisplayName" "${{APP_NAME}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "UninstallString" '"$INSTDIR\\Uninstall.exe"'
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "DisplayVersion" "${{APP_VERSION}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "Publisher" "${{APP_PUBLISHER}}"
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "NoModify" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}" "NoRepair" 1

    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\\${{APP_NAME}}"
    CreateShortcut "$SMPROGRAMS\\${{APP_NAME}}\\${{APP_NAME}}.lnk" "$INSTDIR\\${{APP_EXE}}"
    CreateShortcut "$SMPROGRAMS\\${{APP_NAME}}\\Uninstall.lnk" "$INSTDIR\\Uninstall.exe"
    CreateShortcut "$DESKTOP\\${{APP_NAME}}.lnk" "$INSTDIR\\${{APP_EXE}}"
SectionEnd

; Uninstaller Section
Section "Uninstall"
    ; Remove files
    Delete "$INSTDIR\\${{APP_EXE}}"
    Delete "$INSTDIR\\Uninstall.exe"

    ; Remove shortcuts
    Delete "$SMPROGRAMS\\${{APP_NAME}}\\*.*"
    Delete "$DESKTOP\\${{APP_NAME}}.lnk"
    RMDir "$SMPROGRAMS\\${{APP_NAME}}"

    ; Remove directories
    RMDir "$INSTDIR"

    ; Remove registry keys
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APP_NAME}}"
    DeleteRegKey HKLM "Software\\${{APP_NAME}}"
SectionEnd
"""

    nsis_file = project_root / "build_scripts" / "installer.nsi"
    with open(nsis_file, 'w') as f:
        f.write(nsis_script)

    return nsis_file

def create_installer():
    """Create NSIS installer."""
    print("\nCreating NSIS installer...")

    # Check if NSIS is installed
    nsis_compiler = shutil.which("makensis")
    if nsis_compiler is None:
        print("WARNING: NSIS not found. Download from https://nsis.sourceforge.io/")
        print("Skipping installer creation")
        return False

    # Create NSIS script
    nsis_script = create_nsis_script()
    print(f"Created NSIS script: {nsis_script}")

    # Compile installer
    cmd = [nsis_compiler, str(nsis_script)]
    print(f"Running: makensis...")
    result = subprocess.run(cmd, cwd=project_root)

    if result.returncode != 0:
        print("ERROR: NSIS compilation failed")
        return False

    installer_path = project_root / "dist" / f"TicketeraBuena-Setup-{__version__}.exe"
    if installer_path.exists():
        print(f"\n✓ Successfully created: {installer_path}")
        print(f"  Size: {installer_path.stat().st_size / (1024*1024):.2f} MB")
        return True
    else:
        print("ERROR: Installer not found after compilation")
        return False

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
        print("  Consider activating venv: venv\\Scripts\\activate")

    print("✓ Dependency check complete\n")

def main():
    parser = argparse.ArgumentParser(description="Build TicketeraBuena for Windows")
    parser.add_argument("--installer", action="store_true", help="Create NSIS installer")
    parser.add_argument("--clean", action="store_true", help="Clean build directories first")
    args = parser.parse_args()

    print("=" * 60)
    print(f"TicketeraBuena Windows Build Script v{__version__}")
    print("=" * 60)

    # Verify we're on Windows
    if sys.platform != "win32":
        print("WARNING: This script is designed for Windows")
        print("Continuing anyway, but installer creation may not work")

    # Verify dependencies
    verify_dependencies()

    # Clean if requested
    if args.clean:
        clean_build_dirs()

    # Build the executable
    if not build_exe():
        return 1

    # Create installer if requested
    if args.installer:
        create_installer()

    print("\n" + "=" * 60)
    print("Build complete!")
    print("=" * 60)
    print(f"\nOutput:")
    print(f"  Executable: dist/TicketeraBuena.exe")
    if args.installer:
        print(f"  Installer: dist/TicketeraBuena-Setup-{__version__}.exe")
    print("\nNext steps:")
    print("  1. Test the application: dist\\TicketeraBuena.exe")
    print("  2. Distribute the installer (if created)")
    print("  3. Publish update using: python build_scripts/publish_update.py")

    return 0

if __name__ == "__main__":
    sys.exit(main())
