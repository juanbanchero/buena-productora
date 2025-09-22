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
import json
import getpass
import hashlib
from pathlib import Path
from cryptography.fernet import Fernet
import base64

class CredentialManager:
    def __init__(self, app_name="buena-live"):
        self.app_name = app_name
        self.credentials_file = self._get_credentials_path()
        self._encryption_key = self._generate_key()

    def _get_credentials_path(self):
        """Genera la ruta del archivo de credenciales específica por usuario/app"""
        # Usar el directorio actual del proyecto para hacer las credenciales específicas
        current_dir = os.path.basename(os.getcwd())
        username = getpass.getuser()

        # Crear directorio oculto en home del usuario
        home_dir = Path.home()
        app_dir = home_dir / f".{self.app_name}_{username}_{current_dir}"
        app_dir.mkdir(exist_ok=True)

        return app_dir / "user_credentials.enc"

    def _generate_key(self):
        """Genera una clave de encriptación específica por usuario/máquina/app"""
        # Combinar información del sistema para generar clave única
        username = getpass.getuser()
        current_dir = os.path.abspath(os.getcwd())

        # Crear seed único para esta instalación/usuario
        seed = f"{username}:{current_dir}:{self.app_name}".encode()
        key_hash = hashlib.sha256(seed).digest()

        # Convertir a clave Fernet válida
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
        """Carga credenciales automáticamente si existen"""
        try:
            if not os.path.exists(self.credentials_file):
                return None, None

            fernet = Fernet(self._encryption_key)

            # Leer y desencriptar
            with open(self.credentials_file, 'rb') as f:
                encrypted_data = f.read()

            decrypted_data = fernet.decrypt(encrypted_data)
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