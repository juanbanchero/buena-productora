# Guía de Build para BuenaLive

## ⚠️ IMPORTANTE: Verificación Antes del Build

### Paso 1: Verificar el entorno virtual

```bash
# Asegurarte de estar en el directorio del proyecto
cd /Users/juanbanchero/Proyectos/buena-live

# Activar el entorno virtual
source venv/bin/activate  # En Mac/Linux
# o
venv\Scripts\activate  # En Windows

# Verificar que Python esté usando el venv
which python  # Debe mostrar: /Users/juanbanchero/Proyectos/buena-live/venv/bin/python
```

### Paso 2: Verificar que todos los módulos estén instalados

```bash
# Instalar dependencias (si no lo has hecho)
pip install -r requirements.txt

# Verificar que todos los módulos necesarios estén disponibles
python check_imports.py
```

**Resultado esperado:**
```
✓ tkinter
✓ gspread
✓ google.oauth2.service_account
✓ selenium
✓ webdriver_manager
✓ cryptography
✓ wsgiref  ← CRÍTICO para OAuth
✓ httplib2
✓ requests
✓ trio
...
✅ Todos los módulos necesarios están disponibles!
```

**Si faltan módulos:**
```bash
pip install --upgrade -r requirements.txt
```

---

## 🔨 Build en macOS

### Paso 3: Limpiar builds anteriores (opcional pero recomendado)

```bash
rm -rf build/ dist/ *.spec~
```

### Paso 4: Ejecutar PyInstaller

```bash
pyinstaller buena-live.spec
```

**Salida esperada (sin errores):**
```
229 INFO: PyInstaller: 6.16.0
...
Including credentials.json: /Users/.../credentials.json  ← Si existe
...
Building BUNDLE...
Building BUNDLE... completed successfully.
```

### Paso 5: Probar el ejecutable

```bash
# Ejecutar la app
./dist/TicketeraBuena.app/Contents/MacOS/TicketeraBuena

# O abrir normalmente
open dist/TicketeraBuena.app
```

**Si la app no abre:**
```bash
# Ver logs de errores
./dist/TicketeraBuena.app/Contents/MacOS/TicketeraBuena 2>&1 | tee app_errors.log
```

---

## 🪟 Build en Windows

### Preparación adicional para Windows

1. **Instalar Visual C++ Redistributable** (si no está instalado):
   - https://aka.ms/vs/17/release/vc_redist.x64.exe

2. **Verificar Python 3.11+ (NO 3.13 todavía - mejor compatibilidad)**:
   ```cmd
   python --version
   ```

### Build en Windows

```cmd
# Activar entorno virtual
venv\Scripts\activate

# Verificar módulos
python check_imports.py

# Build
pyinstaller buena-live.spec

# Probar
dist\TicketeraBuena.exe
```

---

## 🚨 Solución de Problemas Comunes

### Error: "ModuleNotFoundError: No module named 'wsgiref'"

**Causa:** El módulo `wsgiref` fue excluido por error en versiones anteriores del `.spec`

**Solución:** Ya está corregido en `buena-live.spec`. Asegúrate de usar la versión actualizada.

---

### Error: "Unable to find credentials.json"

**Causa:** El archivo `credentials.json` no existe en tu directorio

**Solución:**
- Si tienes el archivo, colócalo en el directorio raíz del proyecto
- Si no lo tienes, el build seguirá funcionando (solo mostrará un WARNING)
- La app necesitará el archivo en runtime para funcionar con Google Sheets

---

### Error: "No module named 'google_auth_oauthlib'"

**Causa:** Falta la dependencia en tu entorno

**Solución:**
```bash
pip install google-auth-oauthlib
```

---

### Error en Windows: "DLL load failed"

**Causa:** Problemas con UPX compression en Windows

**Solución:** Ya está deshabilitado en el `.spec` (línea 244: `upx=False`)

---

### La app se cierra inmediatamente sin mensaje

**Causa:** Error en runtime no capturado

**Solución:** Ejecutar desde terminal para ver el error:
```bash
# Mac
./dist/TicketeraBuena.app/Contents/MacOS/TicketeraBuena

# Windows
dist\TicketeraBuena.exe
```

---

## ✅ Checklist Final Antes de Distribuir

- [ ] `python check_imports.py` pasa sin errores
- [ ] `pyinstaller buena-live.spec` completa sin errores
- [ ] La app abre correctamente
- [ ] La app puede conectarse a Google Sheets (si tienes credentials.json)
- [ ] La automatización de Selenium funciona
- [ ] Probar en una máquina limpia (sin Python instalado)

---

## 📦 Archivos Generados

Después del build exitoso:

**macOS:**
- `dist/TicketeraBuena.app/` - Aplicación bundle completa
- Tamaño: ~150-200 MB

**Windows:**
- `dist/TicketeraBuena.exe` - Ejecutable único
- Tamaño: ~80-120 MB

---

## 🔍 Verificación de Módulos Incluidos

Para verificar qué módulos están incluidos en el ejecutable:

```bash
# Mac
./dist/TicketeraBuena.app/Contents/MacOS/TicketeraBuena --debug

# Windows
dist\TicketeraBuena.exe --debug
```

O revisar manualmente los archivos empaquetados:

```bash
# Mac - ver contenido del bundle
ls -la dist/TicketeraBuena.app/Contents/MacOS/

# Windows - extraer y revisar
# (Usar una herramienta como 7-Zip para abrir el .exe)
```

---

## 📝 Notas Importantes

1. **Python 3.13**: Estás usando Python 3.13.7, que es muy reciente. Si tienes problemas, considera usar Python 3.11 o 3.12 que tienen mejor soporte en PyInstaller.

2. **Módulos críticos agregados en esta versión**:
   - ✅ `wsgiref` - Requerido para OAuth
   - ✅ `google_auth_oauthlib` - Autenticación OAuth
   - ✅ `httplib2` - Cliente HTTP para Google APIs
   - ✅ `trio` - Async support para Selenium 4.x

3. **Módulos excluidos** (para reducir tamaño):
   - ❌ `pandas`, `numpy` - No se usan en el código
   - ❌ `pytest`, testing frameworks
   - ❌ `matplotlib`, PyQt - GUIs no usadas

4. **Compatibilidad multiplataforma**: El mismo `.spec` funciona para Mac y Windows, pero debes hacer el build en cada plataforma.

---

## 🆘 Si Nada Funciona

1. **Borrar todo y empezar de cero:**
   ```bash
   # Limpiar completamente
   rm -rf venv/ build/ dist/

   # Crear nuevo entorno
   python3.11 -m venv venv  # Usar 3.11 si 3.13 da problemas
   source venv/bin/activate

   # Instalar dependencias
   pip install --upgrade pip
   pip install -r requirements.txt

   # Verificar
   python check_imports.py

   # Build
   pyinstaller buena-live.spec
   ```

2. **Contactar para ayuda con logs:**
   - Copiar la salida completa de `pyinstaller buena-live.spec`
   - Copiar la salida de `python check_imports.py`
   - Compartir el error exacto que ves
