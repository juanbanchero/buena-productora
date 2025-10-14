#!/usr/bin/env python3
"""
Script para verificar que todos los módulos necesarios estén disponibles.
Esto simula lo que PyInstaller necesitará en runtime.
"""

import sys

modules_to_check = [
    # === MÓDULOS USADOS DIRECTAMENTE ===
    # Tkinter (stdlib - GUI)
    'tkinter',

    # Google Sheets & Auth (main.py:40)
    'gspread',
    'google.oauth2.service_account',
    'google.auth',

    # Selenium (main.py:4-12)
    'selenium',
    'selenium.webdriver.common.by',
    'selenium.webdriver.support.ui',
    'selenium.webdriver.chrome.service',
    'selenium.common.exceptions',

    # WebDriver Manager (main.py:12)
    'webdriver_manager',
    'webdriver_manager.chrome',

    # Cryptography (credential_manager.py:6)
    'cryptography',
    'cryptography.fernet',

    # Packaging (updater.py:4)
    'packaging',

    # === DEPENDENCIAS CRÍTICAS OCULTAS ===
    # WSGI - REQUERIDO por google-auth-oauthlib
    'wsgiref',
    'wsgiref.simple_server',
    'http.server',

    # HTTP clients
    'httplib2',
    'requests',
    'urllib3',

    # OAuth (requerido por gspread)
    'google_auth_oauthlib',
    'oauthlib',
    'requests_oauthlib',

    # Async (requerido por Selenium 4.x)
    'trio',
    'sniffio',

    # === STDLIB CRÍTICOS ===
    'email',
    'json',
    'base64',
    'hashlib',
    'socket',
    'ssl',
    'html.parser',
    'xml.etree.ElementTree',
    'urllib.parse',
    'webbrowser',
    'logging',
]

print("Verificando módulos necesarios para PyInstaller...\n")

missing = []
available = []

for module in modules_to_check:
    try:
        __import__(module)
        available.append(module)
        print(f"✓ {module}")
    except ImportError as e:
        missing.append(module)
        print(f"✗ {module} - {e}")

print(f"\n{'='*60}")
print(f"Disponibles: {len(available)}/{len(modules_to_check)}")
print(f"Faltantes: {len(missing)}/{len(modules_to_check)}")

if missing:
    print(f"\n⚠️  FALTAN {len(missing)} módulos:")
    for m in missing:
        print(f"  - {m}")
    sys.exit(1)
else:
    print("\n✅ Todos los módulos necesarios están disponibles!")
    sys.exit(0)
