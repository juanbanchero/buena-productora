"""
BuenaLive automation main application with GUI and headless ticket purchasing.

This module provides the core automation engine for BuenaLive ticket purchasing
with a Tkinter-based GUI interface. Integrates web automation, credential management,
and Google Sheets tracking for comprehensive ticket automation.

Key classes:
    - TicketAutomation: Core automation engine with Selenium WebDriver
    - AutomationGUI: Tkinter-based user interface with credential management

Key features:
    - Web automation for ticket detection and purchasing
    - Secure credential management with automatic encryption
    - Google Sheets integration for purchase tracking
    - Both GUI and headless operation modes
    - Real-time logging and status monitoring

Integration points:
    - Uses CredentialManager for secure credential storage
    - Connects to Google Sheets via gspread for data logging
    - Controls Chrome WebDriver for web automation

See Also:
    - credential_manager.py: Secure credential handling
    - credentials.json: Google Sheets API service account
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import gspread
from google.oauth2.service_account import Credentials
import time
import os
from datetime import datetime
import sys
import re
from credential_manager import CredentialManager
from version import __version__
import updater

class TicketAutomation:
    def __init__(self, headless_mode=True):
        self.driver = None
        self.sheet = None
        self.credentials_file = "credentials.json"
        self.log_text = None
        self.selected_event = None
        self.current_row = None
        self.headless_mode = headless_mode  # Configuración para producción
        
    def setup_driver(self):
        """Configura el driver de Chrome con optimizaciones de performance"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')

        # Configuración headless mode
        if self.headless_mode:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--window-size=1920,1080')

        # Optimizaciones de performance para procesamiento masivo
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-javascript-harmony-shipping')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-client-side-phishing-detection')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--memory-pressure-off')
        
        try:
            # Usar webdriver-manager para descargar automáticamente el ChromeDriver correcto
            # Esto funciona en Mac, Windows y Linux sin configuración adicional
            self.log("Configurando ChromeDriver automáticamente...")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.log("✓ ChromeDriver configurado correctamente")
                
            # Configurar timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(5)
                
            self.log("✓ Driver configurado correctamente")
            return True
        except Exception as e:
            self.log(f"✗ Error configurando driver: {str(e)}")
            return False
        
    def login(self, email, password):
        """Realiza el login en el sistema"""
        try:
            self.log("Iniciando login...")
            self.driver.get("https://pos.buenalive.com/")
            
            # Esperar y completar email
            email_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_input.clear()
            email_input.send_keys(email)
            
            # Completar password
            password_input = self.driver.find_element(By.ID, "password")
            password_input.clear()
            password_input.send_keys(password)
            
            # Click en submit
            submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit' and contains(., 'Ingresar')]")
            submit_button.click()
            
            # Seleccionar Backoffice
            backoffice_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//h2[contains(text(),'Backoffice')]"))
            )
            backoffice_button.click()

            # Verificar que el login fue exitoso esperando elemento del dashboard
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//li[contains(@class, 'block overflow-hidden rounded bg-white')] | //div[contains(@class, 'grid')] | //main"))
            )

            self.log("✓ Login exitoso")
            return True
            
        except Exception as e:
            self.log(f"✗ Error en login: {str(e)}")
            return False
    
    def get_available_events(self):
        """Obtiene la lista de eventos disponibles"""
        try:
            self.log("Obteniendo eventos disponibles...")
            
            events = []
            event_cards = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'block overflow-hidden rounded bg-white')]")
            
            for card in event_cards:
                try:
                    event_name = card.find_element(By.XPATH, ".//a[contains(@class, 'font-semibold')]").text
                    emitir_button = card.find_element(By.XPATH, ".//a[contains(., 'Emitir stock')]")
                    event_href = emitir_button.get_attribute('href')
                    event_id = event_href.split('/events/')[1].split('/')[0]
                    
                    events.append({
                        'name': event_name,
                        'id': event_id,
                        'href': event_href,
                        'element': emitir_button
                    })
                    
                    self.log(f"  • {event_name} (ID: {event_id})")
                    
                except Exception as e:
                    continue
                    
            return events
            
        except Exception as e:
            self.log(f"✗ Error obteniendo eventos: {str(e)}")
            return []
            
    def connect_google_sheets(self, sheet_url):
        """Conecta con Google Sheets"""
        try:
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            
            if not os.path.exists(self.credentials_file):
                self.log("✗ No se encuentra el archivo credentials.json de Google")
                return None
                
            creds = Credentials.from_service_account_file(self.credentials_file, scopes=scope)
            client = gspread.authorize(creds)
            
            if '/d/' in sheet_url:
                sheet_id = sheet_url.split('/d/')[1].split('/')[0]
            else:
                sheet_id = sheet_url
                
            self.sheet = client.open_by_key(sheet_id)
            self.log(f"✓ Conectado a Google Sheets")
            return self.sheet
            
        except Exception as e:
            self.log(f"✗ Error conectando Google Sheets: {str(e)}")
            return None
    
    def wait_and_click(self, xpath, timeout=None, description="elemento"):
        """Helper para esperar y clickear un elemento con timeout optimizado"""
        # Timeout dinámico basado en modo headless (más rápido en headless)
        if timeout is None:
            timeout = 3 if self.headless_mode else 5

        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            # En modo headless, usar JavaScript para clickear
            if self.headless_mode:
                self.driver.execute_script("arguments[0].click();", element)
            else:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                element.click()
            return True
        except TimeoutException:
            self.log(f"  ⚠ No se encontró {description}, intentando continuar...")
            return False
        except Exception as e:
            self.log(f"  ⚠ Error clickeando {description}: {str(e)}")
            return False
    
    def wait_and_send_keys(self, identifier, value, by=By.ID, timeout=None, description="campo"):
        """Helper para esperar y escribir en un campo con timeout optimizado"""
        # Timeout dinámico basado en modo headless
        if timeout is None:
            timeout = 3 if self.headless_mode else 5

        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, identifier))
            )
            element.clear()
            element.send_keys(value)
            return True
        except TimeoutException:
            self.log(f"  ⚠ No se encontró {description}")
            return False
        except Exception as e:
            self.log(f"  ⚠ Error en {description}: {str(e)}")
            return False

    def check_duplicate_dni_error_fast(self):
        """Detecta error DNI duplicado con JavaScript rápido y recupera automáticamente"""
        try:
            # JavaScript más rápido que XPath para detectar el error
            js_check = """
            var alerts = document.querySelectorAll('div[role="alert"]');
            for (var i = 0; i < alerts.length; i++) {
                if (alerts[i].textContent.includes('duplicatedDocuments')) {
                    return true;
                }
            }
            return false;
            """

            # Verificar inmediatamente después de click
            for attempt in range(4):  # 4 intentos de 0.5s = 2 segundos total
                if self.driver.execute_script(js_check):
                    self.log(f"⚠️ DNI duplicado detectado (intento {attempt + 1}) - regresando a página de emisión")

                    # RECUPERACIÓN: Navegar directamente a página de emisión
                    try:
                        if self.selected_event:
                            self.driver.get(f"https://pos.buenalive.com/events/{self.selected_event['id']}/sale")

                            # Esperar que la página se cargue
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.XPATH,
                                    "//button[contains(@id, 'headlessui-listbox-button')] | //input | //form"))
                            )
                            self.log("  ✓ Página de emisión lista para siguiente ticket")
                    except Exception as recovery_error:
                        self.log(f"  ⚠ Error en recuperación: {str(recovery_error)}")

                    return True
                time.sleep(0.5)

            return False
        except Exception as e:
            self.log(f"Error en verificación rápida: {str(e)}")
            return False


    def emitir_ticket_completo(self, row_data, row_number):
        """Proceso completo de emisión de ticket siguiendo el flujo exacto"""
        start_time = time.time()  # Inicio del timer de performance
        try:
            self.log(f"\n=== Procesando fila {row_number}: {row_data.get('Nombre')} {row_data.get('Apellido')} ===")
            
            # PASO 1: Seleccionar función
            funcion = str(row_data.get('Función', '')).strip()
            if funcion:
                self.log(f"1. Seleccionando función: {funcion}")
            else:
                self.log("1. Seleccionando función (primera disponible)...")

            # Click en el primer listbox button (selector de función)
            funcion_buttons = self.driver.find_elements(By.XPATH,
                "//button[contains(@id, 'headlessui-listbox-button') and contains(@class, 'cursor-default')]")

            if len(funcion_buttons) > 0:
                # Click en el primer button (función)
                if self.headless_mode:
                    self.driver.execute_script("arguments[0].click();", funcion_buttons[0])
                else:
                    funcion_buttons[0].click()

                # Esperar que se desplieguen las opciones
                time.sleep(0.3)

                if funcion:
                    # Buscar la función específica por texto exacto o parcial
                    try:
                        # Intentar match exacto primero
                        funcion_option = self.driver.find_element(By.XPATH,
                            f"//li[contains(@id, 'headlessui-listbox-option')]//*[contains(text(), '{funcion}')]/ancestor::li")
                        if self.headless_mode:
                            self.driver.execute_script("arguments[0].click();", funcion_option)
                        else:
                            funcion_option.click()
                        self.log(f"  ✓ Función seleccionada: {funcion}")
                    except:
                        # Si no encuentra, intentar con el texto contenido en el span
                        try:
                            funcion_option = self.driver.find_element(By.XPATH,
                                f"//li[contains(@id, 'headlessui-listbox-option')]//span[contains(text(), '{funcion}')]/ancestor::li")
                            if self.headless_mode:
                                self.driver.execute_script("arguments[0].click();", funcion_option)
                            else:
                                funcion_option.click()
                            self.log(f"  ✓ Función seleccionada: {funcion}")
                        except:
                            # Si no encuentra la función exacta, usar la primera
                            self.log(f"  ⚠ No se encontró '{funcion}', usando primera disponible")
                            self.wait_and_click(
                                "//li[contains(@id, 'headlessui-listbox-option')][1]",
                                timeout=5,
                                description="primera función"
                            )
                else:
                    # Si no hay función especificada, usar la primera
                    self.wait_and_click(
                        "//li[contains(@id, 'headlessui-listbox-option')][1]",
                        timeout=5,
                        description="primera función"
                    )
            
            # PASO 2: Seleccionar sector
            sector = str(row_data.get('Sector', '')).strip()
            if sector:
                self.log(f"2. Seleccionando sector: {sector}")
                # Click en el segundo listbox (sector)
                sector_buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(@id, 'headlessui-listbox-button')]")
                
                if len(sector_buttons) > 1:
                    if self.headless_mode:
                        self.driver.execute_script("arguments[0].click();", sector_buttons[1])
                    else:
                        sector_buttons[1].click()
                    
                    # Buscar y clickear el sector correcto
                    try:
                        # Buscar match parcial del sector
                        sector_option = self.driver.find_element(By.XPATH, 
                            f"//li[contains(@id, 'headlessui-listbox-option')][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{sector.lower()}')]")
                        if self.headless_mode:
                            self.driver.execute_script("arguments[0].click();", sector_option)
                        else:
                            sector_option.click()
                    except:
                        # Si no encuentra, seleccionar el primero
                        self.wait_and_click(
                            "//li[contains(@id, 'headlessui-listbox-option')][1]",
                            timeout=3,
                            description="primer sector disponible"
                        )
            
            # PASO 3: Seleccionar tarifa basada en el valor
            valor = str(row_data.get('Valor', '0')).replace('$', '').replace('.', '').replace(',', '.')
            try:
                valor_float = float(valor)
            except:
                valor_float = 0
            
            self.log(f"3. Seleccionando tarifa (valor: ${valor_float})")
            
            # Click en el combobox de tarifa
            tarifa_input = self.driver.find_element(By.XPATH,
                "//input[contains(@id, 'headlessui-combobox-input')]")
            tarifa_input.click()
            
            # Determinar qué tarifa buscar
            if valor_float > 0:
                tarifas = ["ENTRADAS GENERALES", "Fase", "General"]
            else:
                tarifas = ["Cortesía", "RRPP", "Buena"]
            
            tarifa_seleccionada = False
            for tarifa in tarifas:
                try:
                    tarifa_input.clear()
                    tarifa_input.send_keys(tarifa)
                    
                    # Intentar seleccionar la opción que contiene el texto de la tarifa
                    tarifa_option = self.driver.find_element(By.XPATH,
                        f"//li[contains(@id, 'headlessui-combobox-option') and contains(text(), '{tarifa}')]")
                    if self.headless_mode:
                        self.driver.execute_script("arguments[0].click();", tarifa_option)
                    else:
                        tarifa_option.click()
                    tarifa_seleccionada = True
                    self.log(f"  Tarifa seleccionada: {tarifa}")
                    break
                except:
                    continue
            
            if not tarifa_seleccionada:
                tarifa_input.click()
                self.wait_and_click(
                    "//li[contains(@id, 'headlessui-combobox-option')][1]",
                    timeout=3
                )

            # PASO 4: Cantidad (siempre 1, ya viene por defecto)
            self.log("4. Cantidad: 1 (default)")
            
            # PASO 5: Click en CONTINUAR antes de cargar asistentes
            self.log("5. Haciendo click en Continuar...")
            continuar_clicked = self.wait_and_click(
                "//button[@type='submit' and contains(., 'Continuar') and contains(@class, 'self-end')]",
                timeout=5,
                description="botón Continuar"
            )
            
            if not continuar_clicked:
                # Intentar con otro selector
                self.wait_and_click(
                    "//button[contains(@class, 'bg-primary-600') and contains(., 'Continuar')]",
                    timeout=3,
                    description="botón Continuar alternativo"
                )

            # PASO 6: Cargar asistentes
            self.log("6. Cargando asistentes...")
            cargar_asistentes = self.wait_and_click(
                "//button[contains(., 'Cargar asistentes')]",
                description="botón cargar asistentes"
            )
            
            if cargar_asistentes:
                # Llenar datos del asistente
                nombre = str(row_data.get('Nombre', ''))
                apellido = str(row_data.get('Apellido', ''))

                # Limpiar DNI: solo letras y números (soporta pasaportes alfanuméricos)
                # Convertir a string primero (Google Sheets puede devolver números como int)
                dni_raw = str(row_data.get('DNI', ''))
                dni = re.sub(r'[^a-zA-Z0-9]', '', dni_raw)
                if dni != dni_raw:
                    self.log(f"  DNI limpiado: '{dni_raw}' → '{dni}'")

                # Leer tipo de documento (CI, DNI, Pasaporte, Otro)
                tipo_documento = str(row_data.get('Tipo', 'DNI')).strip()

                # PASO 6b: Seleccionar tipo de documento
                self.log(f"6b. Seleccionando tipo de documento: {tipo_documento}")

                # Click en el tercer listbox (tipo de documento)
                tipo_doc_buttons = self.driver.find_elements(By.XPATH,
                    "//button[contains(@id, 'headlessui-listbox-button')]")

                if len(tipo_doc_buttons) >= 3:
                    # El tercer listbox es el de tipo de documento
                    if self.headless_mode:
                        self.driver.execute_script("arguments[0].click();", tipo_doc_buttons[2])
                    else:
                        tipo_doc_buttons[2].click()

                    # Buscar y clickear el tipo de documento correcto
                    try:
                        # Buscar opción que contenga el tipo de documento
                        tipo_option = self.driver.find_element(By.XPATH,
                            f"//li[contains(@id, 'headlessui-listbox-option') and (text()='{tipo_documento}' or contains(text(), '{tipo_documento}'))]")

                        if self.headless_mode:
                            self.driver.execute_script("arguments[0].click();", tipo_option)
                        else:
                            tipo_option.click()

                        self.log(f"  ✓ Tipo de documento seleccionado: {tipo_documento}")
                    except:
                        # Si no encuentra, seleccionar el primero por defecto
                        self.wait_and_click(
                            "//li[contains(@id, 'headlessui-listbox-option')][1]",
                            timeout=3,
                            description="primer tipo de documento"
                        )
                        self.log(f"  ⚠ No se encontró '{tipo_documento}', usando opción por defecto")
                else:
                    self.log(f"  ⚠ Selector de tipo de documento no encontrado, continuando...")

                self.wait_and_send_keys("holders.0.firstName", nombre, description="nombre")
                self.wait_and_send_keys("holders.0.lastName", apellido, description="apellido")
                self.wait_and_send_keys("holders.0.documentNumber", dni, description="DNI")
                
                # PASO 7: Guardar asistentes
                self.log("7. Guardando asistentes...")
                self.wait_and_click(
                    "//button[@type='submit' and contains(., 'Guardar asistentes')]",
                    description="guardar asistentes"
                )


            # PASO 8: Omitir (si aparece)
            self.log("8. Buscando botón Omitir...")
            self.wait_and_click(
                "//button[@type='submit' and contains(., 'Omitir')]",
                timeout=3,
                description="omitir"
            )

            # PASO 9: Seleccionar Quentro
            self.log("9. Seleccionando Quentro...")
            self.wait_and_click(
                "//button[contains(@class, 'group') and contains(., 'Quentro')]",
                description="Quentro"
            )

            # PASO 10: Seleccionar enviar por email
            self.log("10. Seleccionando enviar por email...")
            self.wait_and_click(
                "//button[contains(@class, 'group') and contains(., 'Enviar por email')]",
                description="enviar por email"
            )
            # PASO 11: Ingresar email y continuar
            email = str(row_data.get('Mail', ''))
            if email:
                self.log(f"11. Ingresando email: {email}")
                self.wait_and_send_keys("email", email, description="email")

                # Click en Continuar después del email
                self.log("11b. Haciendo click en Continuar después del email...")
                continuar_email = self.wait_and_click(
                    "//button[@type='submit' and contains(., 'Continuar') and contains(@class, 'self-end')]",
                    timeout=5,
                    description="botón Continuar después de email"
                )
                
                if not continuar_email:
                    # Intentar selector alternativo
                    self.wait_and_click(
                        "//button[@type='submit' and contains(@class, 'bg-primary-600') and contains(., 'Continuar')]",
                        timeout=3,
                        description="botón Continuar alternativo"
                    )

                # PASO 12: Omitir (si aparece nuevamente)
                self.log("12. Buscando segundo botón Omitir...")
                self.wait_and_click(
                    "//button[contains(@class, 'text-xs') and contains(., 'Omitir')]",
                    timeout=3,
                    description="omitir pequeño"
                )
            
            # PASO 13: Reservar entradas
            self.log("13. Reservando entradas...")
            reservar = self.wait_and_click(
                "//button[contains(., 'Reservar entradas')]",
                description="reservar entradas"
            )
            
            if not reservar:
                self.wait_and_click(
                    "//button[contains(@class, 'bg-primary-600') and contains(@class, 'text-base')]",
                    description="botón principal"
                )

            # VERIFICAR ERROR DNI DUPLICADO INMEDIATAMENTE (antes de esperar carga)
            if self.check_duplicate_dni_error_fast():
                self.log("⚠️ DNI DUPLICADO detectado - marcando error y continuando con siguiente ticket")
                return "ERROR_DNI_DUPLICADO"

            # Solo si no hay error, esperar que aparezcan las opciones de pago
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH,
                        "//div[@role='radiogroup']//p[text()='Cortesía']"))
                )
                self.log("✓ Opciones de pago cargadas correctamente")
                time.sleep(0.5)  # Micro-delay para estabilización
            except TimeoutException:
                self.log("⚠ Opciones de pago tardaron en cargar")

            # PASO 14: Seleccionar Cortesía ANTES de pagar (si el valor es 0)
            if valor_float == 0:
                self.log("14. Seleccionando Cortesía antes del pago...")

                cortesia_seleccionada = self.wait_and_click(
                    "//div[@role='radiogroup']//p[text()='Cortesía']/ancestor::div[@role='radio']",
                    timeout=5,
                    description="botón radio Cortesía"
                )

                if cortesia_seleccionada:
                    self.log("  ✓ Cortesía seleccionada exitosamente")
                else:
                    self.log("  ⚠ No se pudo seleccionar Cortesía, continuando...")
            
            # PASO 15: Pagar
            self.log("15. Confirmando pago...")
            pagar = self.wait_and_click(
                "//button[@type='submit' and contains(., 'Pagar')]",
                description="pagar"
            )
            
            if not pagar:
                self.wait_and_click(
                    "//button[contains(@class, 'bg-primary-600') and (contains(., 'Confirmar') or contains(., 'Finalizar'))]",
                    description="confirmar/finalizar"
                )
            
            # PASO 16: Esperar confirmación y capturar número de ticket
            # Esperar que aparezca el número de ticket (en lugar de sleep de 5 segundos)
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH,
                        "//p[contains(@class, 'text-gray-500') and contains(text(), '#')] | "
                        "//span[contains(text(), '#')] | "
                        "//div[contains(text(), '#')] | "
                        "//*[contains(@class, 'text-sm') and contains(text(), '#')]"))
                )
            except TimeoutException:
                self.log("  ⚠ No se detectó número de ticket rápidamente")

            # PASO 16: Capturar número de ticket
            self.log("16. Capturando número de ticket...")
            ticket_number = self.capture_ticket_number()
            
            if ticket_number:
                duration = time.time() - start_time
                self.log(f"✓ Ticket generado: {ticket_number}")
                self.log(f"⏱️ TICKET {ticket_number} EMITIDO EN {duration:.1f} SEGUNDOS")

                # PASO 17: Realizar otra venta
                self.log("17. Preparando siguiente venta...")
                self.wait_and_click(
                    "//button[contains(., 'Realizar otra venta')]",
                    timeout=5,
                    description="realizar otra venta"
                )

                return ticket_number
            else:
                self.log("✗ No se pudo capturar el número de ticket")
                return None
                
        except Exception as e:
            self.log(f"✗ Error en emisión: {str(e)}")
            # Intentar volver al inicio
            try:
                self.driver.get(f"https://pos.buenalive.com/events/{self.selected_event['id']}/sale")
                # Esperar que la página se cargue antes de continuar
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//button | //input | //form"))
                )
            except:
                pass
            return None

    def emitir_ticket_innominado(self, row_data, row_number):
        """Proceso completo de emisión de ticket innominado (sin datos personales)"""
        start_time = time.time()  # Inicio del timer de performance
        try:
            self.log(f"\n=== Procesando INNOMINADO fila {row_number} ===")

            # PASO 1: Seleccionar función (IDÉNTICO A NOMINADOS)
            funcion = str(row_data.get('Función', '')).strip()
            if funcion:
                self.log(f"1. Seleccionando función: {funcion}")
            else:
                self.log("1. Seleccionando función (primera disponible)...")

            # Click en el primer listbox button (selector de función)
            funcion_buttons = self.driver.find_elements(By.XPATH,
                "//button[contains(@id, 'headlessui-listbox-button') and contains(@class, 'cursor-default')]")

            if len(funcion_buttons) > 0:
                # Click en el primer button (función)
                if self.headless_mode:
                    self.driver.execute_script("arguments[0].click();", funcion_buttons[0])
                else:
                    funcion_buttons[0].click()

                # Esperar que se desplieguen las opciones
                time.sleep(0.3)

                if funcion:
                    # Buscar la función específica por texto exacto o parcial
                    try:
                        # Intentar match exacto primero
                        funcion_option = self.driver.find_element(By.XPATH,
                            f"//li[contains(@id, 'headlessui-listbox-option')]//*[contains(text(), '{funcion}')]/ancestor::li")
                        if self.headless_mode:
                            self.driver.execute_script("arguments[0].click();", funcion_option)
                        else:
                            funcion_option.click()
                        self.log(f"  ✓ Función seleccionada: {funcion}")
                    except:
                        # Si no encuentra, intentar con el texto contenido en el span
                        try:
                            funcion_option = self.driver.find_element(By.XPATH,
                                f"//li[contains(@id, 'headlessui-listbox-option')]//span[contains(text(), '{funcion}')]/ancestor::li")
                            if self.headless_mode:
                                self.driver.execute_script("arguments[0].click();", funcion_option)
                            else:
                                funcion_option.click()
                            self.log(f"  ✓ Función seleccionada: {funcion}")
                        except:
                            # Si no encuentra la función exacta, usar la primera
                            self.log(f"  ⚠ No se encontró '{funcion}', usando primera disponible")
                            self.wait_and_click(
                                "//li[contains(@id, 'headlessui-listbox-option')][1]",
                                timeout=5,
                                description="primera función"
                            )
                else:
                    # Si no hay función especificada, usar la primera
                    self.wait_and_click(
                        "//li[contains(@id, 'headlessui-listbox-option')][1]",
                        timeout=5,
                        description="primera función"
                    )

            # PASO 2: Seleccionar sector (IDÉNTICO A NOMINADOS)
            sector = str(row_data.get('Sector', '')).strip()
            if sector:
                self.log(f"2. Seleccionando sector: {sector}")
                # Click en el segundo listbox (sector)
                sector_buttons = self.driver.find_elements(By.XPATH,
                    "//button[contains(@id, 'headlessui-listbox-button')]")

                if len(sector_buttons) > 1:
                    if self.headless_mode:
                        self.driver.execute_script("arguments[0].click();", sector_buttons[1])
                    else:
                        sector_buttons[1].click()

                    # Buscar y clickear el sector correcto
                    try:
                        # Buscar match parcial del sector
                        sector_option = self.driver.find_element(By.XPATH,
                            f"//li[contains(@id, 'headlessui-listbox-option')][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{sector.lower()}')]")
                        if self.headless_mode:
                            self.driver.execute_script("arguments[0].click();", sector_option)
                        else:
                            sector_option.click()
                    except:
                        # Si no encuentra, seleccionar el primero
                        self.wait_and_click(
                            "//li[contains(@id, 'headlessui-listbox-option')][1]",
                            timeout=3,
                            description="primer sector disponible"
                        )

            # PASO 3: Seleccionar tarifa basada en el valor (IDÉNTICO A NOMINADOS)
            valor = str(row_data.get('Valor', '0')).replace('$', '').replace('.', '').replace(',', '.')
            try:
                valor_float = float(valor)
            except:
                valor_float = 0

            self.log(f"3. Seleccionando tarifa (valor: ${valor_float})")

            # Click en el combobox de tarifa
            tarifa_input = self.driver.find_element(By.XPATH,
                "//input[contains(@id, 'headlessui-combobox-input')]")
            tarifa_input.click()

            # Determinar qué tarifa buscar
            if valor_float > 0:
                tarifas = ["ENTRADAS GENERALES", "Fase", "General"]
            else:
                tarifas = ["Cortesía", "RRPP", "Buena"]

            tarifa_seleccionada = False
            for tarifa in tarifas:
                try:
                    tarifa_input.clear()
                    tarifa_input.send_keys(tarifa)

                    # Intentar seleccionar la opción que contiene el texto de la tarifa
                    tarifa_option = self.driver.find_element(By.XPATH,
                        f"//li[contains(@id, 'headlessui-combobox-option') and contains(text(), '{tarifa}')]")
                    if self.headless_mode:
                        self.driver.execute_script("arguments[0].click();", tarifa_option)
                    else:
                        tarifa_option.click()
                    tarifa_seleccionada = True
                    self.log(f"  Tarifa seleccionada: {tarifa}")
                    break
                except:
                    continue

            if not tarifa_seleccionada:
                tarifa_input.click()
                self.wait_and_click(
                    "//li[contains(@id, 'headlessui-combobox-option')][1]",
                    timeout=3
                )

            # PASO 4: Cantidad (DIFERENTE - Leer y llenar cantidad)
            cantidad = str(row_data.get('Cantidad', '1'))
            self.log(f"4. Ingresando cantidad: {cantidad}")

            # Buscar input de cantidad por diferentes selectores
            cantidad_llenada = self.wait_and_send_keys("quantity", cantidad, timeout=3, description="cantidad")

            if not cantidad_llenada:
                # Intentar con XPath si el selector por ID no funciona
                try:
                    cantidad_input = self.driver.find_element(By.XPATH, "//input[@type='number']")
                    cantidad_input.clear()
                    cantidad_input.send_keys(cantidad)
                    self.log(f"  ✓ Cantidad ingresada: {cantidad}")
                except:
                    self.log(f"  ⚠ No se pudo ingresar cantidad, usando valor por defecto")

            # PASO 5: Click en CONTINUAR (IDÉNTICO A NOMINADOS)
            self.log("5. Haciendo click en Continuar...")
            continuar_clicked = self.wait_and_click(
                "//button[@type='submit' and contains(., 'Continuar') and contains(@class, 'self-end')]",
                timeout=5,
                description="botón Continuar"
            )

            if not continuar_clicked:
                # Intentar con otro selector
                self.wait_and_click(
                    "//button[contains(@class, 'bg-primary-600') and contains(., 'Continuar')]",
                    timeout=3,
                    description="botón Continuar alternativo"
                )

            # PASO 6: OMITIR DIRECTAMENTE (COMPLETAMENTE DIFERENTE)
            self.log("6. Omitiendo carga de asistentes...")
            omitir_clicked = self.wait_and_click(
                "//button[@type='submit' and contains(., 'Omitir')]",
                timeout=5,
                description="botón Omitir"
            )

            if not omitir_clicked:
                # Intentar selector alternativo
                self.wait_and_click(
                    "//button[contains(@class, 'bg-primary-600') and contains(., 'Omitir')]",
                    timeout=3,
                    description="botón Omitir alternativo"
                )

            # PASO 7-16: IDÉNTICO A NOMINADOS (empezando desde paso 8 de nominados)

            # PASO 7: Omitir (si aparece)
            self.log("7. Buscando botón Omitir...")
            self.wait_and_click(
                "//button[@type='submit' and contains(., 'Omitir')]",
                timeout=3,
                description="omitir"
            )

            # PASO 8: Seleccionar Quentro
            self.log("8. Seleccionando Quentro...")
            self.wait_and_click(
                "//button[contains(@class, 'group') and contains(., 'Quentro')]",
                description="Quentro"
            )

            # PASO 9: Seleccionar enviar por email
            self.log("9. Seleccionando enviar por email...")
            self.wait_and_click(
                "//button[contains(@class, 'group') and contains(., 'Enviar por email')]",
                description="enviar por email"
            )

            # PASO 10: Ingresar email y continuar
            email = str(row_data.get('Mail', ''))
            if email:
                self.log(f"10. Ingresando email: {email}")
                self.wait_and_send_keys("email", email, description="email")

                # Click en Continuar después del email
                self.log("10b. Haciendo click en Continuar después del email...")
                continuar_email = self.wait_and_click(
                    "//button[@type='submit' and contains(., 'Continuar') and contains(@class, 'self-end')]",
                    timeout=5,
                    description="botón Continuar después de email"
                )

                if not continuar_email:
                    # Intentar selector alternativo
                    self.wait_and_click(
                        "//button[@type='submit' and contains(@class, 'bg-primary-600') and contains(., 'Continuar')]",
                        timeout=3,
                        description="botón Continuar alternativo"
                    )

                # PASO 11: Omitir (si aparece nuevamente)
                self.log("11. Buscando segundo botón Omitir...")
                self.wait_and_click(
                    "//button[contains(@class, 'text-xs') and contains(., 'Omitir')]",
                    timeout=3,
                    description="omitir pequeño"
                )

            # PASO 12: Reservar entradas
            self.log("12. Reservando entradas...")
            reservar = self.wait_and_click(
                "//button[contains(., 'Reservar entradas')]",
                description="reservar entradas"
            )

            if not reservar:
                self.wait_and_click(
                    "//button[contains(@class, 'bg-primary-600') and contains(@class, 'text-base')]",
                    description="botón principal"
                )

            # VERIFICAR ERROR DNI DUPLICADO INMEDIATAMENTE (antes de esperar carga)
            if self.check_duplicate_dni_error_fast():
                self.log("⚠️ DNI DUPLICADO detectado - marcando error y continuando con siguiente ticket")
                return "ERROR_DNI_DUPLICADO"

            # Solo si no hay error, esperar que aparezcan las opciones de pago
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH,
                        "//div[@role='radiogroup']//p[text()='Cortesía']"))
                )
                self.log("✓ Opciones de pago cargadas correctamente")
                time.sleep(0.5)  # Micro-delay para estabilización
            except TimeoutException:
                self.log("⚠ Opciones de pago tardaron en cargar")

            # PASO 13: Seleccionar Cortesía ANTES de pagar (si el valor es 0)
            if valor_float == 0:
                self.log("13. Seleccionando Cortesía antes del pago...")

                cortesia_seleccionada = self.wait_and_click(
                    "//div[@role='radiogroup']//p[text()='Cortesía']/ancestor::div[@role='radio']",
                    timeout=5,
                    description="botón radio Cortesía"
                )

                if cortesia_seleccionada:
                    self.log("  ✓ Cortesía seleccionada exitosamente")
                else:
                    self.log("  ⚠ No se pudo seleccionar Cortesía, continuando...")

            # PASO 14: Pagar
            self.log("14. Confirmando pago...")
            pagar = self.wait_and_click(
                "//button[@type='submit' and contains(., 'Pagar')]",
                description="pagar"
            )

            if not pagar:
                self.wait_and_click(
                    "//button[contains(@class, 'bg-primary-600') and (contains(., 'Confirmar') or contains(., 'Finalizar'))]",
                    description="confirmar/finalizar"
                )

            # PASO 15: Esperar confirmación y capturar número de ticket
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH,
                        "//p[contains(@class, 'text-gray-500') and contains(text(), '#')] | "
                        "//span[contains(text(), '#')] | "
                        "//div[contains(text(), '#')] | "
                        "//*[contains(@class, 'text-sm') and contains(text(), '#')]"))
                )
            except TimeoutException:
                self.log("  ⚠ No se detectó número de ticket rápidamente")

            # PASO 16: Capturar número de ticket
            self.log("15. Capturando número de ticket...")
            ticket_number = self.capture_ticket_number()

            if ticket_number:
                duration = time.time() - start_time
                self.log(f"✓ Ticket innominado generado: {ticket_number}")
                self.log(f"⏱️ TICKET INNOMINADO {ticket_number} EMITIDO EN {duration:.1f} SEGUNDOS")

                # PASO 17: Realizar otra venta
                self.log("16. Preparando siguiente venta...")
                self.wait_and_click(
                    "//button[contains(., 'Realizar otra venta')]",
                    timeout=5,
                    description="realizar otra venta"
                )

                return ticket_number
            else:
                self.log("✗ No se pudo capturar el número de ticket innominado")
                return None

        except Exception as e:
            self.log(f"✗ Error en emisión innominada: {str(e)}")
            # Intentar volver al inicio
            try:
                self.driver.get(f"https://pos.buenalive.com/events/{self.selected_event['id']}/sale")
                # Esperar que la página se cargue antes de continuar
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//button | //input | //form"))
                )
            except:
                pass
            return None

    def capture_ticket_number(self):
        """Captura el número de ticket de la confirmación"""
        try:
            patterns = [
                "//p[contains(@class, 'text-gray-500') and contains(text(), '#')]",
                "//span[contains(text(), '#')]",
                "//div[contains(text(), '#')]",
                "//*[contains(@class, 'text-sm') and contains(text(), '#')]"
            ]
            
            for pattern in patterns:
                try:
                    elements = self.driver.find_elements(By.XPATH, pattern)
                    for elem in elements:
                        text = elem.text.strip()
                        if '#' in text and any(c.isdigit() for c in text):
                            match = re.search(r'#\d+', text)
                            if match:
                                return match.group()
                except:
                    continue
            
            return None
            
        except Exception as e:
            self.log(f"Error capturando ticket: {str(e)}")
            return None
    
    def process_nominadas(self, worksheet_name="Nominadas"):
        """Procesa todos los tickets nominados"""
        try:
            worksheet = self.sheet.worksheet(worksheet_name)
            records = worksheet.get_all_records()
            
            self.log(f"\n{'='*50}")
            self.log(f"Iniciando procesamiento de {len(records)} registros")
            self.log(f"{'='*50}\n")
            
            # Obtener índices de columnas
            headers = worksheet.row_values(1)
            resultado_col = headers.index('Resultado') + 1 if 'Resultado' in headers else len(headers)
            codigo_col = headers.index('Código') + 1 if 'Código' in headers else len(headers) + 1
            
            processed = 0
            errors = 0
            skipped = 0
            
            for idx, row in enumerate(records, start=2):
                try:
                    # Verificar si ya fue procesado
                    if row.get('Código') and str(row.get('Código')).startswith('#'):
                        self.log(f"Fila {idx}: Ya procesado ({row.get('Código')}), saltando...")
                        skipped += 1
                        continue
                    
                    # Verificar datos mínimos
                    if not row.get('DNI'):
                        self.log(f"Fila {idx}: Sin DNI, saltando...")
                        worksheet.update_cell(idx, resultado_col, 'Error - Sin DNI')
                        errors += 1
                        continue
                    
                    # Emitir ticket
                    ticket_number = self.emitir_ticket_completo(row, idx)

                    if ticket_number == "ERROR_DNI_DUPLICADO":
                        # Marcar error específico de DNI duplicado
                        worksheet.update_cell(idx, resultado_col, 'Error - DNI duplicado')
                        errors += 1
                        self.log(f"⚠️ DNI duplicado registrado - continuando con siguiente ticket")
                    elif ticket_number:
                        # Actualizar el sheet con éxito
                        worksheet.update_cell(idx, resultado_col, 'Procesado')  # Estado en Resultado
                        worksheet.update_cell(idx, codigo_col, ticket_number)   # Número en Código
                        processed += 1
                        self.log(f"✓ Ticket emitido y actualizado en Sheet: {ticket_number}")
                    else:
                        # Marcar error genérico de procesamiento
                        worksheet.update_cell(idx, resultado_col, 'Error - No se procesó')
                        errors += 1
                        self.log(f"⚠️ Error genérico: ticket_number = {ticket_number}")
                    
                    # Pequeña pausa entre emisiones (menos en modo headless)
                    time.sleep(0.5 if self.headless_mode else 1)
                    
                except Exception as e:
                    self.log(f"✗ Error en fila {idx}: {str(e)}")
                    try:
                        worksheet.update_cell(idx, resultado_col, f'Error: {str(e)[:30]}')
                    except:
                        pass
                    errors += 1
            
            # Resumen final
            self.log(f"\n{'='*50}")
            self.log(f"RESUMEN DE PROCESAMIENTO:")
            self.log(f"  • Procesados exitosamente: {processed}")
            self.log(f"  • Errores: {errors}")
            self.log(f"  • Saltados (ya procesados): {skipped}")
            self.log(f"  • Total: {len(records)}")
            self.log(f"{'='*50}\n")
            
        except Exception as e:
            self.log(f"✗ Error general: {str(e)}")

    def process_innominadas(self, worksheet_name="Innominadas"):
        """Procesa todos los tickets innominados"""
        try:
            # Intentar "Innominadas" primero, luego "innominadas"
            try:
                worksheet = self.sheet.worksheet(worksheet_name)
            except:
                worksheet = self.sheet.worksheet(worksheet_name.lower())

            records = worksheet.get_all_records()

            self.log(f"\n{'='*50}")
            self.log(f"Iniciando procesamiento de {len(records)} tickets INNOMINADOS")
            self.log(f"{'='*50}\n")

            # Obtener índices de columnas
            headers = worksheet.row_values(1)
            resultado_col = headers.index('Resultado') + 1 if 'Resultado' in headers else len(headers)
            codigo_col = headers.index('Código') + 1 if 'Código' in headers else len(headers) + 1

            processed = 0
            errors = 0
            skipped = 0

            for idx, row in enumerate(records, start=2):
                try:
                    # Verificar si ya fue procesado
                    if row.get('Código') and str(row.get('Código')).startswith('#'):
                        self.log(f"Fila {idx}: Ya procesado ({row.get('Código')}), saltando...")
                        skipped += 1
                        continue

                    # VALIDACIÓN DIFERENTE: Verificar Cantidad
                    cantidad = str(row.get('Cantidad', '0'))
                    try:
                        cantidad_int = int(cantidad)
                    except:
                        cantidad_int = 0

                    if cantidad_int <= 0:
                        self.log(f"Fila {idx}: Cantidad inválida o 0, saltando...")
                        worksheet.update_cell(idx, resultado_col, 'Error - Cantidad inválida')
                        errors += 1
                        continue

                    # LLAMAR FUNCIÓN INNOMINADA
                    ticket_number = self.emitir_ticket_innominado(row, idx)

                    if ticket_number == "ERROR_DNI_DUPLICADO":
                        # Marcar error específico de DNI duplicado
                        worksheet.update_cell(idx, resultado_col, 'Error - DNI duplicado')
                        errors += 1
                        self.log(f"⚠️ DNI duplicado registrado - continuando con siguiente ticket")
                    elif ticket_number:
                        # Actualizar el sheet con éxito
                        worksheet.update_cell(idx, resultado_col, 'Procesado')  # Estado en Resultado
                        worksheet.update_cell(idx, codigo_col, ticket_number)   # Número en Código
                        processed += 1
                        self.log(f"✓ Ticket innominado emitido y actualizado en Sheet: {ticket_number}")
                    else:
                        # Marcar error genérico de procesamiento
                        worksheet.update_cell(idx, resultado_col, 'Error - No se procesó')
                        errors += 1
                        self.log(f"⚠️ Error genérico: ticket_number = {ticket_number}")

                    # Pequeña pausa entre emisiones (menos en modo headless)
                    time.sleep(0.5 if self.headless_mode else 1)

                except Exception as e:
                    self.log(f"✗ Error en fila {idx}: {str(e)}")
                    try:
                        worksheet.update_cell(idx, resultado_col, f'Error: {str(e)[:30]}')
                    except:
                        pass
                    errors += 1

            # Resumen final
            self.log(f"\n{'='*50}")
            self.log(f"RESUMEN DE PROCESAMIENTO INNOMINADOS:")
            self.log(f"  • Procesados exitosamente: {processed}")
            self.log(f"  • Errores: {errors}")
            self.log(f"  • Saltados (ya procesados): {skipped}")
            self.log(f"  • Total: {len(records)}")
            self.log(f"{'='*50}\n")

        except Exception as e:
            self.log(f"✗ Error general innominados: {str(e)}")

    def log(self, message):
        """Loguea mensajes en la interfaz y consola"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        if self.log_text:
            self.log_text.insert(tk.END, log_message + "\n")
            self.log_text.see(tk.END)
            self.log_text.update()

# Interfaz gráfica con opción de headless
class AutomationGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"Ticketera Buena v{__version__}")
        self.root.geometry("700x800")
        self.automation = None
        self.available_events = []
        self.credential_manager = CredentialManager()
        self.updater_instance = None
        self.setup_ui()

        # Check for updates on startup (after 3 seconds, non-blocking)
        self.root.after(3000, self.check_for_updates_silently)
        
    def setup_ui(self):
        # Frame de credenciales
        cred_frame = ttk.LabelFrame(self.root, text="Credenciales", padding="10")
        cred_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(cred_frame, text="Email:").grid(row=0, column=0, sticky="w", pady=5)
        self.email_entry = ttk.Entry(cred_frame, width=40)
        self.email_entry.grid(row=0, column=1, pady=5)

        ttk.Label(cred_frame, text="Contraseña:").grid(row=1, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(cred_frame, width=40, show="*")
        self.password_entry.grid(row=1, column=1, pady=5)

        # Checkbox para guardar credenciales
        self.save_credentials_var = tk.BooleanVar()
        self.save_credentials_checkbox = ttk.Checkbutton(
            cred_frame,
            text="Guardar credenciales",
            variable=self.save_credentials_var,
            command=self.on_save_credentials_toggle
        )
        self.save_credentials_checkbox.grid(row=2, column=1, sticky="w", pady=5)

        # Auto-cargar credenciales si existen
        self.load_saved_credentials()

        # Frame de actualizaciones
        update_frame = ttk.LabelFrame(self.root, text="Actualizaciones", padding="10")
        update_frame.pack(fill="x", padx=10, pady=5)

        # Version info and update button
        update_info_frame = tk.Frame(update_frame)
        update_info_frame.pack(fill="x")

        ttk.Label(update_info_frame, text=f"Versión actual: {__version__}").pack(side="left", padx=5)

        self.check_updates_button = ttk.Button(
            update_info_frame,
            text="Buscar actualizaciones",
            command=self.check_for_updates_ui
        )
        self.check_updates_button.pack(side="left", padx=5)

        # Update status label
        self.update_status_label = ttk.Label(update_frame, text="")
        self.update_status_label.pack(fill="x", pady=5)

        # Progress bar (hidden by default)
        self.update_progress = ttk.Progressbar(
            update_frame,
            mode='indeterminate',
            length=300
        )

        # Frame de Google Sheets
        sheet_frame = ttk.LabelFrame(self.root, text="Google Sheets", padding="10")
        sheet_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(sheet_frame, text="URL del Sheet:").grid(row=0, column=0, sticky="w", pady=5)
        self.sheet_entry = ttk.Entry(sheet_frame, width=50)
        self.sheet_entry.grid(row=0, column=1, pady=5)
        
        # Frame de selección de evento
        self.event_frame = ttk.LabelFrame(self.root, text="Selección de Evento", padding="10")
        self.event_frame.pack(fill="x", padx=10, pady=5)
        
        self.event_listbox = tk.Listbox(self.event_frame, height=10)
        self.event_listbox.pack(fill="x", pady=5)
        
        self.get_events_button = ttk.Button(self.event_frame, text="Refrescar Eventos",
                                           command=self.get_events, state="disabled")
        self.get_events_button.pack(pady=5)
        

        # Botones de acción
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.connect_button = ttk.Button(button_frame, text="1. Conectar Sistemas", 
                                        command=self.connect_systems)
        self.connect_button.pack(side="left", padx=5)
        
        self.start_button = ttk.Button(button_frame, text="Iniciar Emisión Nominados",
                                      command=self.start_processing, state="disabled")
        self.start_button.pack(side="left", padx=5)

        self.start_innominados_button = ttk.Button(button_frame, text="Iniciar Emisión Innominados",
                                                   command=self.start_processing_innominados, state="disabled")
        self.start_innominados_button.pack(side="left", padx=5)

        # Log area
        log_frame = ttk.LabelFrame(self.root, text="Log de Procesamiento", padding="10")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15)
        self.log_text.pack(fill="both", expand=True)
        
        # Crear automation con el modo inicial
        self.automation = TicketAutomation(headless_mode=False)
        self.automation.log_text = self.log_text
        
        # Instrucciones
        self.automation.log("=== INSTRUCCIONES ===")
        self.automation.log("1. Ingresá tus credenciales de BuenaLive")
        self.automation.log("2. Pegá la URL del Google Sheet")
        self.automation.log("3. Hacé click en 'Conectar Sistemas'")
        self.automation.log("4. Los eventos se cargarán automáticamente")
        self.automation.log("5. Seleccioná el evento y hacé click en 'Iniciar Procesamiento'")
        self.automation.log("=====================\n")

    def load_saved_credentials(self):
        """Carga automáticamente las credenciales guardadas al startup"""
        email, password = self.credential_manager.load_credentials()
        if email and password:
            self.email_entry.insert(0, email)
            self.password_entry.insert(0, password)
            self.save_credentials_var.set(True)
            if self.automation:
                self.automation.log("✓ Credenciales guardadas cargadas automáticamente")

    def on_save_credentials_toggle(self):
        """Maneja el toggle del checkbox de guardar credenciales"""
        if not self.save_credentials_var.get():
            # Si el usuario desmarca, eliminar credenciales guardadas
            self.credential_manager.clear_credentials()
            if self.automation:
                self.automation.log("✓ Credenciales eliminadas")
    
    def connect_systems(self):
        """Conecta con el sistema y Google Sheets"""
        email = self.email_entry.get()
        password = self.password_entry.get()
        sheet_url = self.sheet_entry.get()
        
        if not email or not password:
            messagebox.showerror("Error", "Completá email y contraseña")
            return
        
        if not sheet_url:
            messagebox.showerror("Error", "Ingresá la URL del Google Sheet")
            return
        
        # Cerrar driver anterior si existe
        if self.automation and self.automation.driver:
            self.automation.driver.quit()
        
        # Crear nueva instancia con headless mode siempre activado para máximo rendimiento
        self.automation = TicketAutomation(headless_mode=True)
        self.automation.log_text = self.log_text
            
        self.connect_button.config(state="disabled")
        
        thread = threading.Thread(target=self._connect_thread, 
                                 args=(email, password, sheet_url))
        thread.daemon = True
        thread.start()
    
    def _connect_thread(self, email, password, sheet_url):
        """Thread de conexión"""
        try:
            if not self.automation.setup_driver():
                messagebox.showerror("Error", "No se pudo configurar el driver")
                return
                
            if not self.automation.login(email, password):
                messagebox.showerror("Error", "No se pudo hacer login")
                return

            # Guardar credenciales automáticamente después de login exitoso
            if self.save_credentials_var.get():
                if self.credential_manager.update_credentials_if_changed(email, password):
                    self.automation.log("✓ Credenciales guardadas automáticamente")

            if not self.automation.connect_google_sheets(sheet_url):
                messagebox.showerror("Error", "No se pudo conectar a Google Sheets")
                return
            
            self.automation.log("✓ Sistemas conectados exitosamente")
            self.automation.log("Obteniendo eventos automáticamente...")

            # Obtener eventos automáticamente después del login exitoso
            self.get_events()

            self.get_events_button.config(state="normal")
            
        except Exception as e:
            self.automation.log(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))
        finally:
            self.connect_button.config(state="normal")
    
    def get_events(self):
        """Obtiene y muestra los eventos disponibles"""
        self.event_listbox.delete(0, tk.END)
        self.available_events = self.automation.get_available_events()
        
        if self.available_events:
            for event in self.available_events:
                self.event_listbox.insert(tk.END, f"{event['name']} (ID: {event['id']})")

            self.start_button.config(state="normal")
            self.start_innominados_button.config(state="normal")
            self.automation.log(f"✓ {len(self.available_events)} eventos encontrados")
            self.automation.log("Seleccioná un evento y dale a 'Iniciar Emisión Nominados' o 'Iniciar Emisión Innominados'")
        else:
            messagebox.showwarning("Advertencia", "No se encontraron eventos")
    
    def start_processing(self):
        """Inicia el procesamiento de tickets"""
        selection = self.event_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Seleccioná un evento primero")
            return
        
        selected_index = selection[0]
        selected_event = self.available_events[selected_index]
        self.automation.selected_event = selected_event
        
        self.start_button.config(state="disabled")
        
        thread = threading.Thread(target=self._process_thread, 
                                 args=(selected_event,))
        thread.daemon = True
        thread.start()
    
    def _process_thread(self, selected_event):
        """Thread de procesamiento"""
        try:
            # Ir a la página de emisión del evento
            self.automation.driver.get(f"https://pos.buenalive.com/events/{selected_event['id']}/sale")

            # Esperar que la página de emisión esté lista
            WebDriverWait(self.automation.driver, 10).until(
                EC.presence_of_element_located((By.XPATH,
                    "//button[contains(@id, 'headlessui-listbox-button')] | //input | //form"))
            )
            
            # Procesar tickets nominados
            self.automation.process_nominadas()
            
            messagebox.showinfo("Éxito", "Procesamiento completado. Revisá el log para ver el resumen.")
            
        except Exception as e:
            self.automation.log(f"Error crítico: {str(e)}")
            messagebox.showerror("Error", f"Error crítico: {str(e)}")
        finally:
            self.start_button.config(state="normal")

    def start_processing_innominados(self):
        """Inicia el procesamiento de tickets innominados"""
        selection = self.event_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Seleccioná un evento primero")
            return

        selected_index = selection[0]
        selected_event = self.available_events[selected_index]
        self.automation.selected_event = selected_event

        self.start_innominados_button.config(state="disabled")

        thread = threading.Thread(target=self._process_thread_innominados,
                                 args=(selected_event,))
        thread.daemon = True
        thread.start()

    def _process_thread_innominados(self, selected_event):
        """Thread de procesamiento de innominados"""
        try:
            # Ir a la página de emisión del evento
            self.automation.driver.get(f"https://pos.buenalive.com/events/{selected_event['id']}/sale")

            # Esperar que la página de emisión esté lista
            WebDriverWait(self.automation.driver, 10).until(
                EC.presence_of_element_located((By.XPATH,
                    "//button[contains(@id, 'headlessui-listbox-button')] | //input | //form"))
            )

            # Procesar tickets INNOMINADOS
            self.automation.process_innominadas()

            messagebox.showinfo("Éxito", "Procesamiento de innominados completado. Revisá el log para ver el resumen.")

        except Exception as e:
            self.automation.log(f"Error crítico innominados: {str(e)}")
            messagebox.showerror("Error", f"Error crítico: {str(e)}")
        finally:
            self.start_innominados_button.config(state="normal")

    def check_for_updates_silently(self):
        """Check for updates on startup without blocking UI"""
        def check():
            try:
                update_available, latest_version = updater.check_for_updates()
                if update_available:
                    # Show non-intrusive notification
                    self.root.after(0, self._show_startup_update_notification, latest_version)
            except Exception:
                # Fail silently on startup check
                pass

        thread = threading.Thread(target=check, daemon=True)
        thread.start()

    def _show_startup_update_notification(self, latest_version):
        """Show update notification from startup check"""
        self.update_status_label.config(
            text=f"¡Nueva versión {latest_version} disponible! Click en 'Buscar actualizaciones'"
        )
        # Optionally show dialog (less intrusive than auto-download)
        response = messagebox.askyesno(
            "Actualización disponible",
            f"Nueva versión {latest_version} disponible.\n"
            f"Versión actual: {__version__}\n\n"
            f"¿Abrir página de descarga?",
            icon='info'
        )
        if response:
            updater.open_download_page()
            self.update_status_label.config(
                text=f"Descargá v{latest_version} desde tu navegador"
            )

    def check_for_updates_ui(self):
        """Check for updates from the UI"""
        self.check_updates_button.config(state="disabled")
        self.update_status_label.config(text="Verificando actualizaciones...")
        self.update_progress.pack(pady=5)
        self.update_progress.start(10)

        thread = threading.Thread(target=self._check_updates_thread)
        thread.daemon = True
        thread.start()

    def _check_updates_thread(self):
        """Thread for checking updates"""
        try:
            update_available, latest_version = updater.check_for_updates()

            if update_available:
                self.root.after(0, self._show_update_dialog, latest_version)
            else:
                self.root.after(0, self._no_update_available)

        except Exception as e:
            self.root.after(0, self._update_error, str(e))

    def _show_update_dialog(self, latest_version):
        """Show dialog when update is available"""
        self.update_progress.stop()
        self.update_progress.pack_forget()
        self.update_status_label.config(
            text=f"¡Nueva versión disponible: {latest_version}!"
        )
        self.check_updates_button.config(state="normal")

        response = messagebox.askyesno(
            "Actualización disponible",
            f"Nueva versión {latest_version} disponible.\n"
            f"Versión actual: {__version__}\n\n"
            f"¿Abrir página de descarga?"
        )

        if response:
            updater.open_download_page()
            self.update_status_label.config(
                text=f"Descargá v{latest_version} desde tu navegador"
            )

    def _no_update_available(self):
        """Handle no update available"""
        self.update_progress.stop()
        self.update_progress.pack_forget()
        self.update_status_label.config(text="La aplicación está actualizada")
        self.check_updates_button.config(state="normal")
        messagebox.showinfo("Sin actualizaciones", "Ya tenés la última versión instalada.")

    def _update_error(self, error_message):
        """Handle update check error"""
        self.update_progress.stop()
        self.update_progress.pack_forget()
        self.update_status_label.config(text="Error al verificar actualizaciones")
        self.check_updates_button.config(state="normal")
        messagebox.showerror(
            "Error",
            f"No se pudo verificar actualizaciones:\n{error_message}"
        )

    def run(self):
        def on_closing():
            if self.automation and self.automation.driver:
                self.automation.driver.quit()
            self.root.destroy()

        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        self.root.mainloop()

if __name__ == "__main__":
    app = AutomationGUI()
    app.run()