# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for BuenaLive Auto-Updater application.

This spec file defines how the application should be packaged for distribution.
It includes all necessary dependencies, data files, and configuration for both
Mac and Windows platforms.

Usage:
    pyinstaller buena-live.spec

Output:
    - dist/BuenaLive.app (macOS)
    - dist/BuenaLive.exe (Windows)
"""

import sys
import os
from pathlib import Path

block_cipher = None

# Get the application directory (SPECPATH is provided by PyInstaller)
app_dir = Path(SPECPATH)

# Define data files to include (non-Python files needed by app)
datas = [
    (str(app_dir / 'credentials.json'), '.'),  # Google Sheets credentials
    (str(app_dir / 'version.py'), '.'),         # Version information
]

# Define binaries to include (platform-specific executables)
binaries = []
# Include ChromeDriver on Windows if available
if sys.platform == 'win32':
    chromedriver_path = app_dir / 'chromedriver.exe'
    if chromedriver_path.exists():
        binaries.append((str(chromedriver_path), '.'))
        print(f"Including ChromeDriver: {chromedriver_path}")

# Hidden imports (modules not automatically detected by PyInstaller)
hiddenimports = [
    'gspread',
    'google.oauth2.service_account',
    'selenium',
    'selenium.webdriver.common.by',
    'selenium.webdriver.support.ui',
    'selenium.webdriver.support.expected_conditions',
    'selenium.webdriver.chrome.service',
    'selenium.webdriver.chrome.options',
    'cryptography',
    'packaging',
    'requests',
    'webdriver_manager',
    'webdriver_manager.chrome',
]

# Exclude unnecessary modules to reduce size
excludes = [
    # Development/testing modules
    'pytest', 'unittest', 'test', 'tests',
    # Unused standard library modules
    'pdb', 'doctest', 'difflib', 'pydoc', 'inspect',
    # Web servers not needed
    'http.server', 'wsgiref', 'xmlrpc',
    # Unused networking
    'ftplib', 'imaplib', 'poplib', 'smtplib', 'telnetlib',
    # Unused data formats
    'xml', 'xmlrpc', 'plistlib',
    # GUI frameworks we're not using
    'matplotlib', 'PyQt5', 'PyQt6', 'wx',
    # Database modules not needed
    'sqlite3', 'dbm',
    # Unused compression
    'bz2', 'lzma', 'zipfile', 'tarfile',
    # Development tools
    'setuptools', 'pip', 'distutils',
]

# Analysis: scan the main script and its dependencies
a = Analysis(
    ['main.py'],                    # Main entry point
    pathex=[str(app_dir)],          # Paths to search for imports
    binaries=binaries,              # Binary files (includes chromedriver on Windows)
    datas=datas,                    # Data files defined above
    hiddenimports=hiddenimports,    # Hidden imports defined above
    hookspath=[],                   # Custom hooks directory
    hooksconfig={},                 # Hooks configuration
    runtime_hooks=[],               # Runtime hook scripts
    excludes=excludes,              # Modules to exclude (defined above)
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=2,                     # Python optimization level (removes docstrings)
)

# PYZ: Create Python archive
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# Platform-specific configurations
if sys.platform == 'darwin':
    # macOS configuration
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='TicketeraBuena',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,              # No console window (GUI app)
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='TicketeraBuena',
    )

    # Create macOS .app bundle
    app = BUNDLE(
        coll,
        name='TicketeraBuena.app',
        icon=str(app_dir / 'assets' / 'buena-logo.icns'),
        bundle_identifier='com.ticketera-buena.automation',
        info_plist={
            'CFBundleName': 'TicketeraBuena',
            'CFBundleDisplayName': 'Ticketera Buena',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': 'True',
            'LSMinimumSystemVersion': '10.13.0',
        },
    )

else:
    # Windows configuration (optimized for size and performance)
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='TicketeraBuena',
        debug=False,
        bootloader_ignore_signals=False,
        strip=True,                 # Strip binary for smaller size
        upx=True,                   # Enable UPX compression
        upx_exclude=[
            'vcruntime140.dll',     # Don't compress Windows runtime DLLs
            'python3*.dll',         # Don't compress Python DLL
        ],
        runtime_tmpdir=None,
        console=False,              # No console window (GUI app)
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=str(app_dir / 'assets' / 'buena-logo.ico'),
        # Additional optimization flags
        bootloader_options={
            'append_pkg': False,    # Faster startup
        },
    )
