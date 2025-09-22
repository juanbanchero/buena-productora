---
task: h-guardarCredenciales
branch: feature/guardar-credenciales
status: completed
created: 2025-09-22
modules: [credential_manager, main]
---

# Guardar Credenciales

## Problem/Goal
Las credenciales del script no se guardan. La idea es tener alguna especie de guardado muy simple ya sea tipo json o sqlite donde el usuario pueda seleccionar un checkbox de guardar credenciales. Esto tiene que ser particular para el usuario ya que va a ser entregado este mismo ejecutable a muchos usuarios.

Tu tarea es crear un checkbox donde el usuario pueda guardar sus credenciales y estas queden guardados de forma segura sin que se compartan entre ejecutables.

## Success Criteria
- [x] Que el usuario tenga un checkbox de guardar credenciales.
- [x] Que en cada startup el usuario pueda tener sus credenciales automáticamente.

## Context Files
- credential_manager.py - Complete implementation with encryption
- main.py:19,630,646-657,722-738,782-784 - GUI integration points
- CLAUDE.md - Updated project documentation

## User Notes
- Implementation required transparent encryption without user key management
- Credentials must be isolated per user/executable to prevent sharing
- GUI should have checkbox for save/clear functionality
- Auto-load on startup, auto-save after successful login

## Work Log

### 2025-09-22

#### Completed
- Created credential_manager.py module with Fernet encryption
- Implemented user/machine/project-specific key generation using SHA256
- Added CredentialManager class with save/load/clear/update methods
- Integrated checkbox "Guardar credenciales" in AutomationGUI
- Added automatic credential loading on application startup
- Implemented auto-save after successful login when checkbox is checked
- Added credential clearing when user unchecks the option
- Updated main.py with comprehensive module documentation
- Updated CLAUDE.md with complete project architecture documentation

#### Security Features Implemented
- Transparent encryption using cryptography.fernet library
- Machine/user/project-specific encryption keys prevent credential sharing
- Secure file storage in user home directory (~/.buena-live_{user}_{project}/)
- Automatic credential validation and app-specific verification

#### User Experience Features
- One-click credential saving via checkbox
- Automatic credential population on next application startup
- Seamless integration with existing login flow
- No user intervention required for encryption/decryption
- Clear feedback messages in application logs

#### Technical Implementation
- Added dependency on cryptography library for Fernet encryption
- Implemented error handling with graceful fallbacks
- Created isolated credential storage per user installation
- Added automatic credential update detection for changed passwords