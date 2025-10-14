# ✅ Fix: Selección de Tipo de Documento

## 🎯 Problema

El selector de tipo de documento (DNI, CI, Pasaporte, Otro) no estaba seleccionando correctamente la opción del Google Sheets.

**Log del error:**
```
[10:07:04] 6b. Seleccionando tipo de documento: DNI
[10:07:04]   ⚠ Selector de tipo de documento no encontrado, continuando...
```

---

## 🔍 Análisis del Problema

### HTML del Selector (Headless UI)

**Botón:**
```html
<button class="..." id="headlessui-listbox-button-:rm:" ...>
  <span class="block truncate">DNI</span>  ← Valor actual
  <span class="..."><svg>...</svg></span>   ← Ícono dropdown
</button>
```

**Opciones (aparecen después del click):**
```html
<ul class="..." id="headlessui-listbox-options-:rv:" ...>
  <li class="..." id="headlessui-listbox-option-:r10:" ...>
    <div class="flex items-center space-x-3">
      <span class="font-normal block truncate">DNI</span>  ← Texto aquí
    </div>
  </li>
  <li class="..." id="headlessui-listbox-option-:r11:" ...>
    <div class="flex items-center space-x-3">
      <span class="font-normal block truncate">Pasaporte</span>
    </div>
  </li>
  <li class="..." id="headlessui-listbox-option-:r12:" ...>
    <div class="flex items-center space-x-3">
      <span class="font-normal block truncate">Otro</span>
    </div>
  </li>
</ul>
```

### Problema Original

El código buscaba el texto directamente en el `<li>`:
```python
# ❌ INCORRECTO
tipo_option = self.driver.find_element(By.XPATH,
    f"//li[contains(@id, 'headlessui-listbox-option') and text()='{tipo_documento}']")
```

Pero el texto está dentro de un `<span>` anidado:
```
<li>
  <div>
    <span>DNI</span>  ← El texto está aquí
  </div>
</li>
```

---

## ✅ Solución Implementada

### 1. **XPath Corregido** (Línea 615)

```python
# ✅ CORRECTO - Busca el texto dentro del <span>
tipo_option_xpath = f"//li[contains(@id, 'headlessui-listbox-option')]//span[contains(text(), '{tipo_documento}')]"
```

**Qué hace:**
- `//li[contains(@id, 'headlessui-listbox-option')]` - Encuentra todos los `<li>` del dropdown
- `//span[contains(text(), '{tipo_documento}')]` - Busca el `<span>` que contiene el texto

---

### 2. **Normalización CI → DNI** (Líneas 581-588)

```python
# Leer tipo de documento (CI, DNI, Pasaporte, Otro)
tipo_documento_raw = str(row_data.get('Tipo', 'DNI')).strip()

# Normalizar CI a DNI (son equivalentes en el sistema)
if tipo_documento_raw.upper() == 'CI':
    tipo_documento = 'DNI'
    self.log(f"  Tipo 'CI' normalizado a 'DNI'")
else:
    tipo_documento = tipo_documento_raw
```

**Por qué:** El sistema solo tiene 3 opciones (DNI, Pasaporte, Otro), pero el Google Sheets tiene 4 (DNI, CI, Pasaporte, Otro). CI es equivalente a DNI.

---

### 3. **Logging Mejorado** (Líneas 599-658)

```python
# Antes de abrir dropdown
self.log(f"  Encontrados {len(tipo_doc_buttons)} listbox buttons, usando el 3ro (índice 2)")

# Después de abrir
self.log(f"  ✓ Dropdown de tipo de documento abierto")

# Buscando opción
self.log(f"  Buscando opción con XPath: {tipo_option_xpath}")
self.log(f"  ✓ Opción '{tipo_documento}' encontrada")

# Si falla, mostrar opciones disponibles
opciones = self.driver.find_elements(By.XPATH, "//li[contains(@id, 'headlessui-listbox-option')]//span")
opciones_texto = [opt.text for opt in opciones]
self.log(f"  Opciones disponibles: {opciones_texto}")
```

---

### 4. **Esperas Apropiadas** (Líneas 611, 619-621, 634)

```python
# Esperar a que aparezcan las opciones después del click
time.sleep(0.5)

# Usar WebDriverWait para esperar la opción
tipo_option = WebDriverWait(self.driver, 5).until(
    EC.presence_of_element_located((By.XPATH, tipo_option_xpath))
)

# Esperar a que se cierre el dropdown
time.sleep(0.3)
```

---

### 5. **Manejo de Errores Robusto** (Líneas 636-656)

```python
except Exception as e:
    self.log(f"  ✗ Error seleccionando tipo de documento: {str(e)}")

    # Intentar listar todas las opciones disponibles para debugging
    try:
        opciones = self.driver.find_elements(By.XPATH, "//li[contains(@id, 'headlessui-listbox-option')]//span")
        opciones_texto = [opt.text for opt in opciones]
        self.log(f"  Opciones disponibles: {opciones_texto}")
    except:
        pass

    # Fallback: cerrar el dropdown y continuar con DNI por defecto
    try:
        self.driver.execute_script("document.body.click();")
        time.sleep(0.3)
    except:
        pass

    self.log(f"  ⚠ No se pudo seleccionar '{tipo_documento}', continuando con valor por defecto")
```

---

## 📋 Logs Esperados

### Caso Exitoso (DNI):
```
[10:07:04] 6b. Seleccionando tipo de documento: DNI
[10:07:04]   Encontrados 3 listbox buttons, usando el 3ro (índice 2)
[10:07:04]   ✓ Dropdown de tipo de documento abierto
[10:07:04]   Buscando opción con XPath: //li[contains(@id, 'headlessui-listbox-option')]//span[contains(text(), 'DNI')]
[10:07:04]   ✓ Opción 'DNI' encontrada
[10:07:04]   ✓ Tipo de documento seleccionado: DNI
```

### Caso CI → DNI:
```
[10:07:04] 6b. Seleccionando tipo de documento: CI
[10:07:04]   Tipo 'CI' normalizado a 'DNI'
[10:07:04]   Encontrados 3 listbox buttons, usando el 3ro (índice 2)
[10:07:04]   ✓ Dropdown de tipo de documento abierto
[10:07:04]   ✓ Opción 'DNI' encontrada
[10:07:04]   ✓ Tipo de documento seleccionado: DNI
```

### Caso Pasaporte:
```
[10:07:04] 6b. Seleccionando tipo de documento: Pasaporte
[10:07:04]   Encontrados 3 listbox buttons, usando el 3ro (índice 2)
[10:07:04]   ✓ Dropdown de tipo de documento abierto
[10:07:04]   ✓ Opción 'Pasaporte' encontrada
[10:07:04]   ✓ Tipo de documento seleccionado: Pasaporte
```

### Caso Error (con debugging):
```
[10:07:04] 6b. Seleccionando tipo de documento: DNI
[10:07:04]   Encontrados 3 listbox buttons, usando el 3ro (índice 2)
[10:07:04]   ✓ Dropdown de tipo de documento abierto
[10:07:04]   Buscando opción con XPath: //li[...]
[10:07:04]   ✗ Error seleccionando tipo de documento: Unable to locate element
[10:07:04]   Opciones disponibles: ['DNI', 'Pasaporte', 'Otro']
[10:07:04]   ⚠ No se pudo seleccionar 'DNI', continuando con valor por defecto
```

---

## 🎯 Tipos de Documento Soportados

### Google Sheets → Sistema

| Google Sheets | Sistema      | Comportamiento                |
|---------------|--------------|-------------------------------|
| DNI           | DNI          | ✅ Selecciona DNI             |
| CI            | DNI          | ✅ Normaliza a DNI            |
| Pasaporte     | Pasaporte    | ✅ Selecciona Pasaporte       |
| Otro          | Otro         | ✅ Selecciona Otro            |
| (vacío)       | DNI          | ✅ Usa DNI por defecto        |

---

## ✅ Resultado

- ✅ **Selección correcta** del tipo de documento
- ✅ **XPath robusto** que busca dentro del `<span>` anidado
- ✅ **Normalización CI → DNI** automática
- ✅ **Logging detallado** para debugging
- ✅ **Manejo de errores** con fallback
- ✅ **Esperas apropiadas** para el dropdown

**¡Problema resuelto!** 🎉
