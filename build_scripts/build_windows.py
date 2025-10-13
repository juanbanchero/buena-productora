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

import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# Fix Unicode encoding issues on Windows
if sys.platform == "win32":
    # Force UTF-8 encoding for stdout/stderr on Windows
    import io
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding='utf-8')  # type: ignore
    if isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr.reconfigure(encoding='utf-8')  # type: ignore

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
    """Build the Windows executable using PyInstaller with optimizations."""
    print(f"\nBuilding TicketeraBuena v{__version__} for Windows...")
    print("Optimizations enabled: module exclusions, bytecode optimization")

    # Check if spec file exists
    spec_file = project_root / "buena-live.spec"
    if not spec_file.exists():
        print(f"ERROR: Spec file not found: {spec_file}")
        return False

    print("  Note: UPX compression disabled for Python 3.11+ compatibility")

    # Run PyInstaller with optimizations
    cmd = [
        "pyinstaller",
        "--clean",           # Clean cache and remove temporary files
        "--noconfirm",       # Replace output directory without confirmation
        str(spec_file)
    ]

    print(f"Running: {' '.join(cmd)}")
    print("This may take a few minutes...")

    import time
    start_time = time.time()
    result = subprocess.run(cmd, cwd=project_root)
    build_time = time.time() - start_time

    if result.returncode != 0:
        print("ERROR: PyInstaller build failed")
        return False

    # Check if .exe was created
    exe_path = project_root / "dist" / "TicketeraBuena.exe"
    if not exe_path.exists():
        print(f"ERROR: Executable not found at {exe_path}")
        return False

    exe_size_mb = exe_path.stat().st_size / (1024*1024)
    print(f"\n{'='*60}")
    print(f"[OK] Successfully built: {exe_path}")
    print(f"  Size: {exe_size_mb:.2f} MB")
    print(f"  Build time: {build_time:.1f} seconds")
    print(f"{'='*60}")

    return True

def create_nsis_script():
    """Create NSIS installer script with absolute paths."""
    # Get absolute path to icon for NSIS
    icon_path = (project_root / "assets" / "buena-logo.ico").resolve()
    icon_path_win = str(icon_path).replace('/', '\\')

    # Get absolute path to dist directory
    dist_path = (project_root / "dist").resolve()
    dist_path_win = str(dist_path).replace('/', '\\')

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
OutFile "{dist_path_win}\\TicketeraBuena-Setup-${{APP_VERSION}}.exe"
InstallDir "$PROGRAMFILES\\${{APP_NAME}}"
InstallDirRegKey HKLM "Software\\${{APP_NAME}}" "Install_Dir"
RequestExecutionLevel admin

; Interface Settings
!define MUI_ABORTWARNING
!define MUI_ICON "{icon_path_win}"
!define MUI_UNICON "{icon_path_win}"

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
    File "{dist_path_win}\\${{APP_EXE}}"

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

def verify_icon():
    """Verify that the icon file exists for NSIS."""
    icon_path = project_root / "assets" / "buena-logo.ico"

    if not icon_path.exists():
        print(f"ERROR: Icon file not found: {icon_path}")
        return False

    print(f"[OK] Icon file found: {icon_path}")
    return True

def create_installer():
    """Create NSIS installer."""
    print("\nCreating NSIS installer...")

    # Check if NSIS is installed
    nsis_compiler = shutil.which("makensis")
    if nsis_compiler is None:
        print("WARNING: NSIS not found. Download from https://nsis.sourceforge.io/")
        print("Skipping installer creation")
        return False

    # Verify icon exists
    if not verify_icon():
        print("WARNING: Icon not found. Installer will use default icon.")
        # Continue anyway, NSIS will use default if icon is missing

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
        print(f"\n[OK] Successfully created: {installer_path}")
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

    print("[OK] Dependency check complete\n")

def main():
    parser = argparse.ArgumentParser(description="Build TicketeraBuena for Windows")
    parser.add_argument("--installer", action="store_true", help="Create NSIS installer")
    parser.add_argument("--clean", action="store_true", help="Clean build directories first")
    parser.add_argument("--fast", action="store_true", help="Fast build mode (skip UPX compression for development)")
    args = parser.parse_args()

    # If fast mode, temporarily disable UPX in spec file
    if args.fast:
        print("FAST BUILD MODE: Skipping UPX compression for faster builds")
        # Note: This would require modifying the spec file temporarily
        # For now, we'll just inform the user

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
    installer_success = True
    if args.installer:
        installer_success = create_installer()
        if not installer_success:
            print("\nWARNING: Installer creation failed, but executable was built successfully")
            # Don't fail the build if only installer failed
            # return 1

    print("\n" + "=" * 60)
    print("Build complete!")
    print("=" * 60)
    print(f"\nOutput:")
    print(f"  Executable: dist/TicketeraBuena.exe")
    if args.installer and installer_success:
        print(f"  Installer: dist/TicketeraBuena-Setup-{__version__}.exe")
    print("\nOptimizations applied:")
    print("  ✓ Module exclusions (unittest, sqlite3, xml, etc.)")
    print("  ✓ Python bytecode optimization level 2")
    print("  ✓ Windows-compatible packaging (no UPX/strip for stability)")
    print("\nNext steps:")
    print("  1. Test the application: dist\\TicketeraBuena.exe")
    print("  2. Verify Unicode characters display correctly (✓, ✗, ⚠)")
    print("  3. Distribute the installer (if created)")
    print("  4. Publish update using: python build_scripts/publish_update.py")
    print("\nBuild tips:")
    print("  • Use --clean to force a fresh build")
    print("  • Test on clean Windows system without Python installed")
    print("  • Note: UPX disabled for Python 3.11+ stability")

    return 0

if __name__ == "__main__":
    sys.exit(main())
