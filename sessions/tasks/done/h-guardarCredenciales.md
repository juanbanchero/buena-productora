---
task: m-guardarCredenciales
branch: feature/guardar-credenciales
status: in-progress
created: YYYY-MM-DD
modules: [list of services/modules involved]
---

# Guardar Credenciales

## Problem/Goal
Las credenciales del script no se guardan. La idea es tener alguna especie de guardado muy simple ya sea tipo json o sqlite donde el usuario pueda seleccionar un checkbox de guardar credenciales. Esto tiene que ser particular para el usuario ya que va a ser entregado este mismo ejecutable a muchos usuarios.

Tu tarea es crear un checkbox donde el usuario pueda guardar sus credenciales y estas queden guardados de forma segura sin que se compartan entre ejecutables.

## Success Criteria
- [ ] Que el usuario tenga un checkbox de guardar credenciales.
- [ ] Que en cada startup el usuario pueda tener sus credenciales automáticamente.

## Context Files
<!-- Added by context-gathering agent or manually -->
- @service/file.py:123-145  # Specific lines
- @other/module.py          # Whole file  
- patterns/auth-flow        # Pattern reference

## User Notes
<!-- Any specific notes or requirements from the developer -->

## Work Log
<!-- Updated as work progresses -->
- [YYYY-MM-DD] Started task, initial research