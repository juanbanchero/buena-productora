# Guía de Release y Deploy Automático

## 🚀 Proceso de Release Automático

Este proyecto usa GitHub Actions para construir y publicar releases automáticamente cuando creas un tag.

---

## ✅ Pre-requisitos

### 1. GitHub Secrets Configurados

Debes tener configurado en GitHub → Settings → Secrets and variables → Actions:

- **`GOOGLE_CREDENTIALS`**: Contenido completo de `credentials.json` (para Google Sheets API)

Para agregar el secret:
```bash
# En tu máquina local
cat credentials.json | pbcopy  # macOS
# o
cat credentials.json | xclip -selection clipboard  # Linux

# Luego pegar en GitHub → Settings → Secrets → New repository secret
```

### 2. Repositorio Limpio

Asegúrate de que todos los cambios estén commiteados:
```bash
git status  # Debe estar limpio
git push origin main  # Asegúrate de que todo esté pusheado
```

---

## 🏷️ Crear un Release

### Paso 1: Crear y pushear un tag

```bash
# Crear tag con el número de versión (IMPORTANTE: usar formato v*.*.*)
git tag v1.0.15

# Verificar el tag
git tag -l

# Pushear el tag a GitHub (esto inicia el build automático)
git push origin v1.0.15
```

### Paso 2: Monitorear el Build

1. Ve a GitHub → Actions
2. Verás 3 workflows corriendo en paralelo:
   - **Build macOS** - Construye `.dmg` para Mac
   - **Build Windows** - Construye `.exe` installer para Windows
   - **Create Release** - Espera a que los dos anteriores terminen

### Paso 3: Release Creado

Cuando todo termine (15-20 minutos), tendrás:

- Un release en GitHub → Releases
- Dos archivos adjuntos:
  - `TicketeraBuena-{version}-mac.dmg` (para macOS)
  - `TicketeraBuena-Setup-{version}.exe` (para Windows)

---

## 🔄 Flujo Automático Completo

```
1. git tag v1.0.15 && git push origin v1.0.15
                 ↓
2. GitHub Actions detecta el tag
                 ↓
3. Actualiza version.py automáticamente
                 ↓
4. Build en macOS (paralelo)          Build en Windows (paralelo)
   - Instala Python 3.11               - Instala Python 3.11
   - Instala dependencias              - Instala dependencias
   - Crea credentials.json             - Descarga ChromeDriver
   - Ejecuta build_mac.py              - Crea credentials.json
   - Genera .dmg                       - Ejecuta build_windows.py
                 ↓                                  ↓
                 └──────────────┬───────────────────┘
                                ↓
5. Create Release
   - Descarga .dmg y .exe
   - Crea GitHub Release
   - Adjunta archivos
```

---

## 📋 Checklist Pre-Release

Antes de crear un tag, verifica:

- [ ] Todos los cambios están commiteados
- [ ] Los tests locales pasan (si existen)
- [ ] `python check_imports.py` pasa sin errores
- [ ] El build local funciona: `pyinstaller buena-live.spec`
- [ ] La app funciona correctamente en local
- [ ] `GOOGLE_CREDENTIALS` secret está configurado en GitHub

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'wsgiref'"

**Solución**: Ya corregido en `buena-live.spec`. El módulo `wsgiref` ahora está incluido en `hiddenimports`.

---

### Error: "credentials.json not found"

**Causa**: El secret `GOOGLE_CREDENTIALS` no está configurado en GitHub.

**Solución**:
1. Ve a GitHub → Settings → Secrets → Actions
2. Crea un nuevo secret llamado `GOOGLE_CREDENTIALS`
3. Pega el contenido completo de tu archivo `credentials.json`

---

### Build de macOS falla

**Posibles causas**:
- Python 3.11 no está disponible en el runner
- Dependencias faltantes en `requirements.txt`
- Error en `buena-live.spec`

**Solución**:
1. Revisa los logs en GitHub Actions
2. Busca el error específico
3. Prueba el build localmente en macOS primero

---

### Build de Windows falla

**Posibles causas**:
- ChromeDriver no se descargó correctamente
- NSIS no está instalado (se instala automáticamente con choco)
- Error en `buena-live.spec`

**Solución**:
1. Revisa los logs en GitHub Actions → Build Windows
2. Busca en la sección "Download ChromeDriver" o "Build Windows app"
3. Prueba el build localmente en Windows primero

---

### Release creado pero sin archivos adjuntos

**Causa**: Los workflows de build fallaron pero el workflow de release continuó.

**Solución**:
1. Ve a Actions y revisa qué workflow falló
2. Borra el release fallido en GitHub → Releases
3. Borra el tag: `git tag -d v1.0.X && git push origin :refs/tags/v1.0.X`
4. Corrige el error
5. Crea el tag nuevamente

---

## 🔧 Builds Locales (Desarrollo)

Para probar builds localmente antes del release:

### macOS
```bash
cd /Users/juanbanchero/Proyectos/buena-live
source venv/bin/activate

# Verificar módulos
python check_imports.py

# Build
python build_scripts/build_mac.py --dmg --clean

# Probar
open dist/TicketeraBuena.app
```

### Windows
```cmd
cd C:\Users\...\buena-live
venv\Scripts\activate

# Verificar módulos
python check_imports.py

# Build
python build_scripts/build_windows.py --installer --clean

# Probar
dist\TicketeraBuena.exe
```

---

## 📦 Estructura de Archivos Generados

```
dist/
├── TicketeraBuena-1.0.15-mac.dmg          # macOS installer (GitHub Release)
├── TicketeraBuena-Setup-1.0.15.exe        # Windows installer (GitHub Release)
├── TicketeraBuena.app/                    # macOS app bundle (local)
└── TicketeraBuena.exe                     # Windows executable (local)
```

---

## 🔐 Seguridad

### Credentials.json

- ⚠️ **NUNCA** commitees `credentials.json` al repo
- ✅ Está en `.gitignore`
- ✅ Se inyecta vía GitHub Secrets durante el build
- ✅ Los ejecutables distribuidos incluyen credentials embebidos

### GitHub Actions

- Los workflows solo se ejecutan en tags `v*.*.*`
- Solo los maintainers del repo pueden crear tags
- Los secrets solo son accesibles durante el workflow

---

## 📝 Notas Importantes

1. **Versión automática**: No necesitas actualizar `version.py` manualmente. El workflow lo hace automáticamente desde el tag.

2. **Python 3.11**: El workflow usa Python 3.11 (no 3.13) para mejor compatibilidad con PyInstaller.

3. **Módulos críticos incluidos**:
   - ✅ `wsgiref` - Requerido para OAuth
   - ✅ `google_auth_oauthlib` - Autenticación Google
   - ✅ `httplib2` - Cliente HTTP
   - ✅ `trio` - Async para Selenium 4.x

4. **Tiempo de build**:
   - macOS: ~10-15 minutos
   - Windows: ~10-15 minutos
   - Total: ~20-25 minutos

5. **Artifacts**: Los archivos intermedios (antes del release) se guardan como artifacts en GitHub Actions por 90 días.

---

## 🎯 Ejemplo Completo de Release

```bash
# 1. Terminar cambios
git add .
git commit -m "Fix: wsgiref dependency error"
git push origin main

# 2. Verificar localmente
python check_imports.py
pyinstaller buena-live.spec

# 3. Crear y pushear tag
git tag v1.0.15
git push origin v1.0.15

# 4. Monitorear en GitHub
# Ve a: https://github.com/tu-usuario/buena-live/actions

# 5. Release disponible en ~20 minutos
# Ve a: https://github.com/tu-usuario/buena-live/releases
```

---

## ❓ Preguntas Frecuentes

**P: ¿Puedo hacer un build solo para macOS o solo para Windows?**

R: Sí, pero necesitas modificar el workflow. Por defecto se construyen ambos en paralelo.

**P: ¿Cómo borro un release fallido?**

R:
```bash
# Borrar release en GitHub UI
# Luego borrar el tag:
git tag -d v1.0.15
git push origin :refs/tags/v1.0.15
```

**P: ¿Por qué el workflow usa Python 3.11 y no 3.13?**

R: Python 3.13 es muy reciente y algunas dependencias de PyInstaller aún no están totalmente optimizadas. Python 3.11 tiene mejor compatibilidad.

**P: ¿Los executables incluyen todas las dependencias?**

R: Sí, son ejecutables "standalone" que incluyen:
- Python runtime
- Todas las librerías (gspread, selenium, etc.)
- credentials.json (embebido)
- ChromeDriver (solo en Windows)

**P: ¿Funciona en sistemas sin Python instalado?**

R: Sí, los ejecutables son completamente independientes.

---

## 📞 Soporte

Si tienes problemas con el build automático:

1. Revisa los logs en GitHub Actions
2. Prueba el build localmente primero
3. Verifica que `buena-live.spec` tenga todos los módulos necesarios
4. Consulta `BUILD_GUIDE.md` para troubleshooting detallado
