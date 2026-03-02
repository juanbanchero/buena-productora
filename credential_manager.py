"""
Secure credential management with transparent encryption for BuenaLive automation.

This module provides automatic credential storage and retrieval with user-specific
encryption keys. Credentials are stored securely in the user's home directory
and encrypted using machine/user/project-specific keys to prevent unauthorized access.

Key classes:
    - CredentialManager: Main credential handling with encryption/decryption

Key features:
    - Transparent encryption using Fernet symmetric encryption
    - User/machine/project-specific encryption keys
    - Automatic credential detection and loading
    - Secure file storage in user home directory

Integration points:
    - Used by AutomationGUI for credential persistence
    - Provides transparent save/load for main.py automation

See Also:
    - main.py: Main application that uses credential management
    - cryptography.fernet: Encryption implementation details
"""
import os
import sys
import json
import getpass
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet
import base64

class CredentialManager:
    def __init__(self, app_name="buena-live"):
        self.app_name = app_name
        self._app_dir = self._get_app_dir()
        self.credentials_file = self._get_credentials_path()
        self._encryption_key = self._generate_key()

    def _get_app_dir(self):
        """Get a stable application directory independent of CWD.

        Uses the executable's directory (frozen) or the script's directory (dev)
        instead of os.getcwd(), which changes depending on how the app is launched
        on Windows (double-click, shortcut, cmd, etc.).
        """
        if getattr(sys, 'frozen', False):
            # PyInstaller: use the directory containing the .exe
            return os.path.dirname(sys.executable)
        else:
            # Development: use the directory containing this script
            return os.path.dirname(os.path.abspath(__file__))

    def _get_credentials_path(self):
        """Genera la ruta del archivo de credenciales específica por usuario/app"""
        # Use stable app directory name instead of CWD
        dir_name = os.path.basename(self._app_dir)
        username = getpass.getuser()

        # Crear directorio oculto en home del usuario
        home_dir = Path.home()
        app_dir = home_dir / f".{self.app_name}_{username}_{dir_name}"
        app_dir.mkdir(exist_ok=True)

        return app_dir / "user_credentials.enc"

    def _generate_key(self):
        """Genera una clave de encriptación específica por usuario/máquina/app"""
        # Combinar información del sistema para generar clave única
        username = getpass.getuser()
        # Use stable app directory instead of CWD for consistent key generation
        stable_dir = os.path.abspath(self._app_dir)

        # Crear seed único para esta instalación/usuario
        seed = f"{username}:{stable_dir}:{self.app_name}".encode()
        key_hash = hashlib.sha256(seed).digest()

        # Convertir a clave Fernet válida
        return base64.urlsafe_b64encode(key_hash[:32])

    def _generate_legacy_key(self):
        """Generate key using the old CWD-based method for migration purposes."""
        username = getpass.getuser()
        current_dir = os.path.abspath(os.getcwd())
        seed = f"{username}:{current_dir}:{self.app_name}".encode()
        key_hash = hashlib.sha256(seed).digest()
        return base64.urlsafe_b64encode(key_hash[:32])

    def save_credentials(self, email, password):
        """Guarda credenciales encriptadas automáticamente"""
        try:
            fernet = Fernet(self._encryption_key)

            credentials_data = {
                "email": email,
                "password": password,
                "app": self.app_name
            }

            # Convertir a JSON y encriptar
            json_data = json.dumps(credentials_data).encode()
            encrypted_data = fernet.encrypt(json_data)

            # Guardar en archivo
            with open(self.credentials_file, 'wb') as f:
                f.write(encrypted_data)

            return True

        except Exception as e:
            print(f"Error guardando credenciales: {e}")
            return False

    def load_credentials(self):
        """Carga credenciales automáticamente si existen.

        If decryption fails with the current key, attempts migration from the
        legacy CWD-based key and re-encrypts with the new stable key.
        """
        try:
            if not os.path.exists(self.credentials_file):
                return None, None

            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()

            # Try current key first
            try:
                fernet = Fernet(self._encryption_key)
                decrypted_data = fernet.decrypt(encrypted_data)
            except Exception:
                # Try legacy CWD-based key for migration
                try:
                    legacy_key = self._generate_legacy_key()
                    legacy_fernet = Fernet(legacy_key)
                    decrypted_data = legacy_fernet.decrypt(encrypted_data)
                    # Re-encrypt with new stable key
                    new_fernet = Fernet(self._encryption_key)
                    with open(self.credentials_file, 'wb') as f:
                        f.write(new_fernet.encrypt(decrypted_data))
                    print("Credenciales migradas a clave estable")
                except Exception:
                    print("Error: no se pudieron desencriptar credenciales con ninguna clave")
                    return None, None

            credentials_data = json.loads(decrypted_data.decode())

            # Verificar que sea para esta app
            if credentials_data.get("app") != self.app_name:
                return None, None

            return credentials_data.get("email"), credentials_data.get("password")

        except Exception as e:
            print(f"Error cargando credenciales: {e}")
            return None, None

    def credentials_exist(self):
        """Verifica si existen credenciales guardadas"""
        email, password = self.load_credentials()
        return email is not None and password is not None

    def clear_credentials(self):
        """Elimina credenciales guardadas"""
        try:
            if os.path.exists(self.credentials_file):
                os.remove(self.credentials_file)
            return True
        except Exception as e:
            print(f"Error eliminando credenciales: {e}")
            return False

    def update_credentials_if_changed(self, email, password):
        """Actualiza credenciales solo si son diferentes a las guardadas"""
        saved_email, saved_password = self.load_credentials()

        # Si no hay credenciales guardadas o son diferentes, guardar
        if saved_email != email or saved_password != password:
            return self.save_credentials(email, password)

        return True  # No cambió nada, todo OK