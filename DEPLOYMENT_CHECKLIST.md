# ✅ Checklist de Deployment - BuenaLive

## 🎯 Verificación Completa Antes del Release

### ✅ PASO 1: Verificación Local (Obligatorio)

```bash
cd /Users/juanbanchero/Proyectos/buena-live
source venv/bin/activate

# 1.1 Verificar que todos los módulos estén instalados
python check_imports.py
```

**Resultado esperado:**
```
✅ Todos los módulos necesarios están disponibles!
Disponibles: 36/36
```

**Si falla algún módulo:**
```bash
pip install --upgrade -r requirements.txt
python check_imports.py  # Verificar de nuevo
```

---

### ✅ PASO 2: Build Local de Prueba (Recomendado)

```bash
# 2.1 Limpiar builds anteriores
rm -rf build/ dist/

# 2.2 Hacer build
pyinstaller buena-live.spec

# 2.3 Verificar que se generó correctamente
ls -lh dist/TicketeraBuena.app

# 2.4 Probar la app
./dist/TicketeraBuena.app/Contents/MacOS/TicketeraBuena
```

**Resultado esperado:**
- La app abre sin errores
- La interfaz se muestra correctamente
- Puedes conectarte a Google Sheets (si tienes credentials.json)

---

### ✅ PASO 3: Verificar GitHub Secrets (Primera vez solamente)

```bash
# 3.1 Verificar que tienes el archivo credentials.json
cat credentials.json

# 3.2 Ir a GitHub
# https://github.com/tu-usuario/buena-live/settings/secrets/actions

# 3.3 Verificar que existe el secret: GOOGLE_CREDENTIALS
```

**Si no existe:**
1. Clic en "New repository secret"
2. Name: `GOOGLE_CREDENTIALS`
3. Value: Pegar contenido completo de `credentials.json`
4. Clic en "Add secret"

---

### ✅ PASO 4: Commit y Push de Cambios

```bash
# 4.1 Verificar cambios pendientes
git status

# 4.2 Commit si hay cambios
git add .
git commit -m "Fix: wsgiref dependency + automated version update"

# 4.3 Push a main
git push origin main

# 4.4 Esperar a que GitHub Actions verifique el push
# Ve a: https://github.com/tu-usuario/buena-live/actions
```

---

### ✅ PASO 5: Crear Tag y Desplegar

```bash
# 5.1 Crear tag con la nueva versión
git tag v1.0.15

# 5.2 Verificar el tag
git tag -l v1.0.15

# 5.3 Push del tag (ESTO INICIA EL DEPLOY AUTOMÁTICO)
git push origin v1.0.15
```

**IMPORTANTE:** El formato del tag DEBE ser `v*.*.*` (ej: v1.0.15)

---

### ✅ PASO 6: Monitorear el Deploy

```bash
# 6.1 Abrir GitHub Actions
# https://github.com/tu-usuario/buena-live/actions
```

**Workflows que deben estar corriendo:**
1. ✓ Build macOS (~10-15 min)
2. ✓ Build Windows (~10-15 min)
3. ✓ Create Release (espera a los dos anteriores)

**Qué monitorear:**

#### En "Build macOS":
```
✓ Checkout code
✓ Set up Python (3.11)
✓ Install dependencies
✓ Update version from tag       ← NUEVO: Verifica que actualice version.py
✓ Create credentials.json
✓ Install create-dmg
✓ Build macOS app
✓ Upload artifacts
```

#### En "Build Windows":
```
✓ Checkout code
✓ Set up Python (3.11)
✓ Install dependencies
✓ Update version from tag       ← NUEVO: Verifica que actualice version.py
✓ Install NSIS
✓ Download ChromeDriver
✓ Create credentials.json
✓ Build Windows app
✓ Upload artifacts
```

---

### ✅ PASO 7: Verificar el Release

Después de ~20 minutos, verifica:

```bash
# 7.1 Ir a Releases
# https://github.com/tu-usuario/buena-live/releases

# 7.2 Verificar que exista el release v1.0.15
# 7.3 Verificar que tenga 2 archivos adjuntos:
#     - TicketeraBuena-1.0.15-mac.dmg
#     - TicketeraBuena-Setup-1.0.15.exe
```

---

## 🚨 Si Algo Falla

### Error: "ModuleNotFoundError: No module named 'wsgiref'"

**Estado:** ✅ SOLUCIONADO en `buena-live.spec`

**Módulos agregados:**
- `wsgiref` y submódulos
- `google_auth_oauthlib`
- `httplib2`
- `oauthlib`
- Todos los módulos stdlib necesarios

---

### Error: "Update version from tag" falla

**Causa posible:** Script `update_version.py` no encuentra el tag

**Solución:**
```bash
# Verificar que el tag exista
git describe --tags --exact-match

# Si no funciona, el workflow debería fallar early
# Revisa los logs en GitHub Actions
```

---

### Build de macOS o Windows falla

**Pasos:**
1. Ve a Actions → Click en el workflow fallido
2. Expande el paso que falló
3. Lee el error completo
4. Busca el error en `BUILD_GUIDE.md` o `RELEASE_GUIDE.md`

**Errores comunes:**
- `credentials.json not found` → Verifica GOOGLE_CREDENTIALS secret
- `ModuleNotFoundError` → Verifica `buena-live.spec` hiddenimports
- `ChromeDriver download failed` → Problema temporal, reintenta

---

### Release creado sin archivos

**Causa:** Ambos builds fallaron

**Solución:**
```bash
# 1. Borrar el release en GitHub UI
# 2. Borrar el tag
git tag -d v1.0.15
git push origin :refs/tags/v1.0.15

# 3. Corregir el error (revisar logs de Actions)
# 4. Crear el tag nuevamente
git tag v1.0.15
git push origin v1.0.15
```

---

## 📊 Resumen de Cambios Implementados

### ✅ Archivo `.spec` Actualizado (`buena-live.spec`)

**Módulos críticos agregados a `hiddenimports`:**
```python
# OAuth y Google Auth
'google_auth_oauthlib',
'google_auth_oauthlib.flow',
'google_auth_oauthlib.interactive',
'oauthlib',
'oauthlib.oauth2',
'requests_oauthlib',

# WSGI (CRÍTICO para OAuth flow)
'wsgiref',
'wsgiref.simple_server',
'wsgiref.util',
'wsgiref.headers',
'http.server',

# HTTP clients
'httplib2',

# Stdlib modules
'email', 'json', 'base64', 'hashlib',
'socket', 'ssl', 'html.parser',
'xml.etree.ElementTree', 'urllib.parse'
```

**Removido de `excludes`:**
```python
# Antes: 'wsgiref' estaba excluido ❌
# Ahora: incluido en hiddenimports ✅
```

---

### ✅ Workflow Actualizado (`.github/workflows/build-release.yml`)

**Nuevo step agregado:**
```yaml
- name: Update version from tag
  run: |
    python build_scripts/update_version.py
    echo "Updated to version:"
    grep "__version__" version.py
```

**Beneficios:**
- ✅ Actualiza `version.py` automáticamente desde el tag
- ✅ No necesitas editar `version.py` manualmente antes del release
- ✅ Consistencia entre tag y versión del ejecutable

---

### ✅ Scripts Nuevos Creados

1. **`check_imports.py`**
   - Verifica que todos los módulos necesarios estén instalados
   - Uso: `python check_imports.py`

2. **`build_scripts/update_version.py`**
   - Actualiza `version.py` desde git tags
   - Uso automático en CI/CD
   - Uso manual: `python build_scripts/update_version.py --version 1.0.15`

---

### ✅ Documentación Creada

1. **`BUILD_GUIDE.md`**
   - Guía paso a paso para builds locales
   - Troubleshooting común
   - Checklist pre-build

2. **`RELEASE_GUIDE.md`**
   - Proceso completo de release automático
   - Flujo de CI/CD explicado
   - FAQs y troubleshooting

3. **`DEPLOYMENT_CHECKLIST.md`** (este archivo)
   - Checklist completo de deployment
   - Verificación paso a paso
   - Qué monitorear en cada etapa

---

## 🎯 Próximos Pasos

### Para hacer tu primer release:

```bash
# 1. Verifica módulos
python check_imports.py

# 2. Build local de prueba
pyinstaller buena-live.spec

# 3. Commit cambios
git add .
git commit -m "Ready for release v1.0.15"
git push origin main

# 4. Crear y pushear tag
git tag v1.0.15
git push origin v1.0.15

# 5. Monitorear en GitHub Actions
# https://github.com/tu-usuario/buena-live/actions

# 6. Descargar release después de ~20 min
# https://github.com/tu-usuario/buena-live/releases
```

---

## ✨ Resultado Final

Después de seguir todos los pasos, tendrás:

- ✅ Build de macOS (`.dmg`) funcional en Windows y Mac
- ✅ Build de Windows (`.exe` installer) funcional en Windows y Mac
- ✅ Versión actualizada automáticamente desde el tag
- ✅ Todos los módulos necesarios incluidos (wsgiref, oauth, etc.)
- ✅ Release publicado automáticamente en GitHub
- ✅ Ejecutables listos para distribución

**Tiempo total:** ~20-25 minutos desde que pusheas el tag

---

## 📞 Si Necesitas Ayuda

1. Revisa los logs completos en GitHub Actions
2. Consulta `BUILD_GUIDE.md` para troubleshooting local
3. Consulta `RELEASE_GUIDE.md` para el proceso de CI/CD
4. Verifica que `buena-live.spec` tenga todos los módulos de `check_imports.py`
