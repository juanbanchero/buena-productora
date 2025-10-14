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
    (str(app_dir / 'version.py'), '.'),         # Version information
]

# Add credentials.json if it exists (optional for development builds)
credentials_file = app_dir / 'credentials.json'
if credentials_file.exists():
    datas.append((str(credentials_file), '.'))
    print(f"Including credentials.json: {credentials_file}")
else:
    print("WARNING: credentials.json not found - app will need it at runtime")

# Define binaries to include (platform-specific executables)
binaries = []
# Include ChromeDriver on Windows if available
if sys.platform == 'win32':
    chromedriver_path = app_dir / 'chromedriver.exe'
    if chromedriver_path.exists():
        binaries.append((str(chromedriver_path), '.'))
        print(f"Including ChromeDriver: {chromedriver_path}")

# Hidden imports (modules not automatically detected by PyInstaller)
# Comprehensive list to prevent runtime import errors
hiddenimports = [
    # Google Sheets
    'gspread',
    'gspread.auth',
    'gspread.client',
    'gspread.utils',
    'gspread.exceptions',

    # Google Authentication (CRITICAL - required for Google Sheets)
    'google.oauth2.service_account',
    'google.auth',
    'google.auth.transport',
    'google.auth.transport.requests',
    'google.auth._default',
    'google.auth.crypt',
    'google.auth.crypt._python_rsa',
    'google.oauth2.credentials',
    'google_auth_oauthlib',
    'google_auth_oauthlib.flow',
    'google_auth_oauthlib.interactive',
    'oauthlib',
    'oauthlib.oauth2',
    'requests_oauthlib',

    # Selenium WebDriver
    'selenium',
    'selenium.webdriver.common.by',
    'selenium.webdriver.support.ui',
    'selenium.webdriver.support.expected_conditions',
    'selenium.webdriver.chrome.service',
    'selenium.webdriver.chrome.options',
    'selenium.common.exceptions',
    'selenium.webdriver.remote.remote_connection',
    'selenium.webdriver.remote.webdriver',
    'selenium.webdriver.remote.webelement',

    # Cryptography (CRITICAL - credential_manager.py uses Fernet)
    'cryptography',
    'cryptography.fernet',
    'cryptography.hazmat',
    'cryptography.hazmat.primitives',
    'cryptography.hazmat.backends',
    'cryptography.hazmat.backends.openssl',
    '_cffi_backend',

    # HTTP/HTTPS Networking
    'packaging',
    'httplib2',
    'requests',
    'requests.adapters',
    'requests.auth',
    'requests.models',
    'requests.sessions',
    'requests.utils',

    # urllib3 (required by requests and selenium)
    'urllib3',
    'urllib3.connection',
    'urllib3.response',
    'urllib3._request_methods',
    'urllib3.http2',
    'urllib3.util',
    'urllib3.util.ssl_',
    'urllib3.connectionpool',
    'urllib3.poolmanager',
    'urllib3.exceptions',

    # WebDriver Manager
    'webdriver_manager',
    'webdriver_manager.chrome',
    'webdriver_manager.core',
    'webdriver_manager.core.utils',

    # Async support (Selenium 4.x uses trio)
    'trio._core',
    'trio._socket',
    'sniffio',

    # Standard library modules needed by dependencies
    'zipfile',           # Required by importlib.metadata
    'tarfile',           # Required by webdriver-manager
    'gzip',              # Required by urllib3/requests compression
    'importlib.metadata',
    'webbrowser',        # Required by updater.py
    'logging',           # Required by multiple libraries

    # WSGI modules (CRITICAL - required by google-auth-oauthlib OAuth flow)
    'wsgiref',
    'wsgiref.simple_server',
    'wsgiref.util',
    'wsgiref.headers',
    'http.server',       # Used by wsgiref.simple_server

    # Additional stdlib modules for OAuth and HTTP
    'email',             # Required by httplib2 and http clients
    'email.message',
    'email.parser',
    'json',              # Required by OAuth and API clients
    'base64',            # Required for authentication encoding
    'hashlib',           # Required for cryptographic operations

    # Core networking and parsing modules
    'socket',            # Core networking
    'ssl',               # HTTPS support
    'html',              # HTML parsing (Selenium)
    'html.parser',
    'xml',               # XML parsing (httplib2, gspread)
    'xml.etree',
    'xml.etree.ElementTree',
    'urllib',            # URL handling
    'urllib.parse',
    'urllib.request',
]

# Exclude unnecessary modules to reduce size
# IMPORTANT: Only exclude modules that are truly unused to avoid runtime errors
# ALL modules listed here have been verified as unused by dependencies
excludes = [
    # Development/testing frameworks
    'pytest', 'test', 'tests', '_pytest',

    # Debugging tools
    'pdb', 'pdb++', 'ipdb', 'doctest', 'pydoc',

    # Web servers (not needed - we're a client)
    # NOTE: wsgiref is REQUIRED by google-auth-oauthlib for OAuth flow
    # NOTE: http.server may be used by wsgiref
    'bottle', 'flask', 'django',

    # Unused networking protocols
    'ftplib', 'imaplib', 'poplib', 'smtplib', 'telnetlib',

    # GUI frameworks we're not using (we use tkinter only)
    'matplotlib', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx',

    # Database modules (not needed - we use Google Sheets)
    'dbm', 'sqlite3',

    # Data analysis (pandas is in requirements.txt but COMPLETELY UNUSED)
    'pandas', 'numpy',

    # Unused compression formats (keep zipfile, gzip, tarfile)
    'bz2', 'lzma',

    # Development/packaging tools
    'pip', 'setuptools._distutils',

    # Documentation generators
    'sphinx', 'docutils',
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
    # Windows configuration (optimized for compatibility and stability)
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
        strip=False,                # Keep symbols - stripping causes issues on Windows
        upx=False,                  # Disable UPX - causes DLL loading failures with Python 3.11+
        runtime_tmpdir=None,
        console=False,              # No console window (GUI app)
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=str(app_dir / 'assets' / 'buena-logo.ico'),
    )
