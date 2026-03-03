import threading
from LimpiadorDatos import*
from Llamada_Api_Gemini import *
from ControladorGemini import *
from ControladorBots import *
from DatabaseManager import *
from TelegramBot import *


class Controlador:
    def __init__(self, api_key: str, token: str):
        print("🔍 [DEBUG] Iniciando componentes del Controlador...")
        
        # 1. Rutas y Utilidades
        self.ruta_documentos = "C:/Users/afogu/Desktop/BOT-web/Documentos"
        self.limpiador = LimpiadorDatos()
        
        # 2. Motores (Gemini y DB)
        self.controlador_gemini = ControladorGemini(clave_api=api_key)
        self.db = DatabaseManager()
        self.controlador_bots = ControladorBots()
        
        # 3. Cargar bots existentes de la DB a la RAM
        print("🔍 [DEBUG] Cargando bots desde la base de datos...")
        self.inicializar_todos_los_bots()

        # 4. Configurar Telegram
        print("🔍 [DEBUG] Configurando bot de Telegram...")
        nombres_disponibles = list(self.controlador_bots.diccionario_bots.keys())
        self.bot_telegram = TelegramBot(token=token, controlador=self, lista_bots=nombres_disponibles)
        
        # 5. Lanzar hilo de Telegram
        # daemon=True significa que si el Main muere, este hilo muere también
        self.hilo_telegram = threading.Thread(target=self.bot_telegram.run, daemon=True)
        self.hilo_telegram.start()
        
        print("✅ Controlador inicializado y sistemas activos.")
        
        
    def _procesar_despliegue_bot(self, registro):
        """
        Método privado que contiene la lógica central de despliegue.
        Recibe una tupla/registro de la base de datos (nombre, expl, pdfs, almacen).
        """
        # 1. Desempaquetado consistente con el nuevo esquema de la DB (4 columnas)
        # nombre, explicacion, pdfs, nombre_almacen_gemini
        nombre, expl, pdfs_raw, id_almacen_db = registro
        
        print(f"\n🚀 Procesando Bot: {nombre}")

        # 2. Lógica de Almacén (Sincronización con Google)
        self.controlador_gemini.repositorio.sincronizar_almacenes()
        nombres_en_google = self.controlador_gemini.repositorio.nombres_registrados
        
        if nombre in nombres_en_google:
            id_google_real = self.controlador_gemini.repositorio.obtener_id(nombre)
        else:
            id_google_real = self.controlador_gemini.repositorio.crear_almacen(nombre)

        # Actualizar DB si el ID cambió o es nuevo
        if id_google_real and id_google_real != id_almacen_db:
            self.db.actualizar_id_almacen(nombre, id_google_real)
            id_almacen_db = id_google_real

        # 3. Lógica de PDFs
        lista_pdfs = []
        if pdfs_raw:
            try:
                lista_pdfs = json.loads(pdfs_raw) if "[" in pdfs_raw else [p.strip() for p in pdfs_raw.split(",")]
            except:
                lista_pdfs = []
                
            if lista_pdfs and id_almacen_db:
                # Aquí usamos el token de la configuración global, no del registro
                self.controlador_gemini.sincronizar_biblioteca(id_almacen_db, lista_pdfs)

        # 4. Creación de Instancia en Memoria (Usando tu nueva clase Bot)
        # IMPORTANTE: Ya no enviamos tokens aquí porque la clase Bot no los recibe
        return self.controlador_bots.crear_bot(
            nombre=nombre,
            explicacion=expl,
            nombres_pdf=lista_pdfs,
            id_almacen_gemini=id_almacen_db
        )

    def inicializar_todos_los_bots(self):
        """Carga y despliega todos los bots de la base de datos."""
        registros = self.db.cargar_todos()
        if not registros:
            print("⚠️ No hay bots para procesar.")
            return

        for r in registros:
            try:
                # r[0] es el nombre del bot para el print de error
                self._procesar_despliegue_bot(r)
            except Exception as e:
                print(f"❌ Error procesando {r[0]}: {e}")
        
        print(f"✨ Proceso masivo finalizado. {len(registros)} bots procesados.") 

    def registrar_y_desplegar_nuevo_bot(self, nombre_usuario, explicacion_usuario, lista_pdfs_django):
        
        # --- PASO 1: LIMPIEZA Y GUARDADO FÍSICO ---
        nombre_limpio = self.limpiador.limpiar_nombre_bot(nombre_usuario)
        explicacion_limpia = self.limpiador.limpiar_explicacion(explicacion_usuario)
        
        nombres_pdfs_finales = []

        for archivo_pdf in lista_pdfs_django:
            try:
                nombre_archivo_limpio = self.limpiador.limpiar_archivo_raw(archivo_pdf)
                ruta_final = os.path.join(self.ruta_documentos, nombre_archivo_limpio)
                
                # Guardar físicamente
                with open(ruta_final, 'wb+') as destino:
                    for chunk in archivo_pdf.chunks():
                        destino.write(chunk)
                
                nombres_pdfs_finales.append(nombre_archivo_limpio)
            except Exception as e:
                print(f"❌ Error guardando archivo {archivo_pdf.name}: {e}")

        # --- PASO 2: INSERTAR EN BASE DE DATOS ---
        pdfs_json = json.dumps(nombres_pdfs_finales)
        
        with sqlite3.connect(self.db.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO bots (nombre, explicacion, pdfs, nombre_almacen_gemini)
                VALUES (?, ?, ?, ?)
            ''', (nombre_limpio, explicacion_limpia, pdfs_json, None))
            conn.commit()

        print(f"✅ Bot '{nombre_limpio}' guardado en DB. Iniciando despliegue...")

        # --- PASO 3: LLAMAR A TU FUNCIÓN DE DESPLIEGUE ---
        registro_para_despliegue = (
            nombre_limpio, 
            explicacion_limpia, 
            pdfs_json, 
            None 
        )
        
        # Ejecutamos el despliegue (esto lo mete en la RAM del ControladorBots)
        resultado = self._procesar_despliegue_bot(registro_para_despliegue)

        # --- PASO 4: ACTUALIZACIÓN DE INTERFAZ TELEGRAM ---
        if hasattr(self, 'bot_telegram') and self.bot_telegram:
            # Refrescamos la lista del bot para que incluya al nuevo recién creado
            self.bot_telegram.actualizar_lista_desde_controlador()
            print(f"📲 Menú de Telegram actualizado con el nuevo bot: {nombre_limpio}")

        return resultado

    def eliminar_bot(self, nombre_usuario: str):
        """
        Elimina un bot de todas las capas: Google Gemini, RAM y SQLite,
        y sincroniza la interfaz de Telegram.
        """
        # 1. Limpieza del nombre para asegurar coincidencia en todas las capas
        nombre_limpio = self.limpiador.limpiar_nombre_bot(nombre_usuario)
        print(f"\n🗑️ Iniciando proceso de eliminación total: {nombre_limpio}")

        # 2. CAPA 1: Eliminar Almacén en Google Gemini (Nube)
        try:
            self.controlador_gemini.eliminar_almacen_busqueda(nombre_limpio)
        except Exception as e:
            print(f"⚠️ Aviso: No se pudo confirmar la eliminación en Gemini: {e}")

        # 3. CAPA 2: Eliminar de la RAM (Diccionario del ControladorBots)
        fue_eliminado_ram = self.controlador_bots.eliminar_bot(nombre_limpio)

        if fue_eliminado_ram:
            # 4. CAPA 3: Eliminar de la Base de Datos (SQLite)
            try:
                self.db.eliminar_bot(nombre_limpio)
                print(f"🗄️ Registro '{nombre_limpio}' borrado de la Base de Datos.")
            except Exception as e:
                print(f"⚠️ Error al eliminar de la DB: {e}")

            # 5. SINCRONIZACIÓN: Actualizar la lista de Telegram en tiempo real
            if hasattr(self, 'bot_telegram') and self.bot_telegram:
                # Llamamos a la nueva función centralizada de actualización
                self.bot_telegram.actualizar_lista_desde_controlador()
            
            print(f"✅ Bot '{nombre_limpio}' eliminado completamente.")
            return True
            
        else:
            print(f"❌ El bot '{nombre_limpio}' no se encontró en la memoria local.")
            return False


    def procesar_consulta_bot(self, nombre_bot: str, pregunta: str) -> str:
        """
        Paso final: Extrae el ID del almacén mediante el nombre del bot 
        y ejecuta la consulta RAG con historial vacío.
        """
        # 1. Verificación de existencia en el diccionario de bots
        if nombre_bot not in self.controlador_bots.diccionario_bots:
            print(f"❌ Error: El bot '{nombre_bot}' no está registrado.")
            return "Lo siento, el asistente seleccionado no es válido."

        # 2. Verificación de seguridad
        id_almacen = self.controlador_bots.obtener_id_almacen_por_nombre(nombre_bot)
        if not id_almacen:
            print(f"⚠️ Error: No se pudo obtener el ID de almacén para '{nombre_bot}'.")
            return "Lo siento, este asistente no tiene acceso a sus documentos ahora mismo."

        print(f"🧠 Consultando a {nombre_bot} (Almacén: {id_almacen})...")

        # 3. Historial en blanco (Sin persistencia de usuario)
        historial_vacio = []

        print(f"🧠 Consultando a {nombre_bot} (Almacén: {id_almacen})...")

        # 4. LLAMADA AL CONTROLADOR GEMINI
        # Se envía la pregunta, la lista vacía y el identificador del almacén de archivos
        respuesta = self.controlador_gemini.hacer_pregunta(
            pregunta=pregunta,
            historial=historial_vacio,
            id_almacen=id_almacen
        )

        # 5. Retorno del resultado
        if respuesta:
            return respuesta
        else:
            return "No he podido encontrar información relacionada en los documentos."


    '''
#CREAN TODOS LOS BOTS CON SUSU ALMACENES Y SUS PDF
    def cargar_bots_iniciales(self):
        """
        Lee la base de datos y crea los objetos Bot en memoria.
        """
        print("🔄 Automatizando la creación de bots desde la base de datos...")
        
        # Obtenemos las tuplas de la BD
        registros = self.db.cargar_todos()
        
        for r in registros:
            # Desempaquetamos la tupla según tu estructura:
            # nombre, token_gemini, token_telegram, explicacion, pdfs (json string)
            nombre, t_gemini, t_tele, expl, pdfs_raw, id_almacen= r
            
            # Convertimos el string JSON de los PDFs de nuevo a lista de Python
            lista_pdfs = json.loads(pdfs_raw)
            
            # Mandamos a crear el bot en el controlador de bots
            self.controlador_bots.crear_bot(
                nombre=nombre,
                token_gemini=t_gemini,
                token_telegram=t_tele,
                explicacion=expl,
                nombres_pdf=lista_pdfs,
                id_almacen_gemini=id_almacen
            )
            
        print(f"✨ Se han creado {len(registros)} bots automáticamente.")
    def crear_almacenes_iniciales(self):
        """
        Sincroniza y verifica existencia usando el mapeo en memoria 
        para evitar llamadas innecesarias a la creación.
        """
        print("\n--- 📦 SINCRONIZANDO ALMACENES CON GOOGLE CLOUD ---")
        
        # 2. Obtenemos datos locales
        self.controlador_gemini.repositorio.sincronizar_almacenes()
        registros = self.db.cargar_todos()
        # Esta es la lista de nombres (keys) que ya existen en Google
        nombres_en_google = self.controlador_gemini.repositorio.nombres_registrados
        
        if not registros:
            print("⚠️ No hay bots en la base de datos para procesar.")
            return

        for r in registros:
            nombre_bot = r[0]
            id_actual_db = r[5] 
            
            # --- VERIFICACIÓN DE COINCIDENCIA ---
            if nombre_bot in nombres_en_google:
                # Si ya existe, simplemente recuperamos el ID del diccionario
                print(f"✅ El almacén '{nombre_bot}' ya existe en Google. Saltando creación...")
                id_google_real = self.controlador_gemini.repositorio.obtener_id(nombre_bot)
            else:
                # Solo si NO coincide, llamamos a la función que crea en la API
                print(f"🆕 Creando almacén para '{nombre_bot}' (no encontrado en la nube)...")
                id_google_real = self.controlador_gemini.repositorio.crear_almacen(nombre_bot)

            # --- ACTUALIZACIÓN DE BASE DE DATOS ---
            if id_google_real:
                if id_actual_db != id_google_real:
                    print(f"💾 Actualizando ID en BD para {nombre_bot}...")
                    self.db.actualizar_id_almacen(nombre_bot, id_google_real)
                
                print(f"📡 {nombre_bot} vinculado a: {id_google_real}")
            else:
                print(f"❌ Error: No se pudo obtener ID para {nombre_bot}")

        print("--- ✅ Sincronización finalizada con éxito ---\n")
    def subir_pdf_iniciales(self):
        """
        Lee la columna 'pdfs' de la base de datos, la limpia y
        sincroniza cada archivo con su almacén Gemini correspondiente.
        """
        print("\n--- 📄 INICIANDO SUBIDA DE PDFS DESDE BD ---")
        
        # 1. Cargamos todos los registros (Bots) de la base de datos
        registros = self.db.cargar_todos()

        if not registros:
            print("⚠️ No hay datos en la BD para subir archivos.")
            return

        for r in registros:
            # Según tu captura: 
            # r[0] = nombre (bot), r[4] = pdfs (lista separada por comas), r[5] = nombre_almacen_gemini
            nombre_bot = r[0]
            string_pdfs = r[4]  # El campo 'pdfs' de la imagen
            id_almacen = r[5]   # El ID que ya sincronizamos en crear_almacenes_iniciales

            if not id_almacen:
                print(f"⏩ Saltando {nombre_bot}: No tiene ID de almacén vinculado.")
                continue

            if not string_pdfs or string_pdfs.strip() == "":
                print(f"ℹ️ {nombre_bot} no tiene archivos PDF registrados.")
                continue

            # 2. Convertimos el string de la BD en una lista real
            # Ejemplo: "ley.pdf, sanidad.pdf" -> ["ley.pdf", "sanidad.pdf"]
            lista_archivos = [p.strip() for p in string_pdfs.split(",") if p.strip()]

            if lista_archivos:
                print(f"🚀 Sincronizando {len(lista_archivos)} archivos para el bot: {nombre_bot}...")
                
                # 3. LLAMADA AL CONTROLADOR GEMINI
                # Esta es la función que ya tenemos configurada para limpiar rutas y subir
                self.controlador_gemini.sincronizar_biblioteca(id_almacen, lista_archivos)
            else:
                print(f"ℹ️ {nombre_bot} tiene el campo PDF vacío.")

        print("\n--- ✅ Proceso de subida de archivos finalizado ---\n")       
#CREAR NUEVO BOT CON SU ALMACEN Y SUS PDF
    def crear_bot_individual(self, nombre_bot):
        """
        Busca un bot específico en la base de datos por su nombre
        y lo crea en memoria usando el controlador de bots.
        """
        print(f"🔄 Intentando crear el bot '{nombre_bot}' desde la base de datos...")
        
        # 1. Utilizamos la función que acabamos de crear para buscar en la BD
        datos_bot = self.db.obtener_bot_por_nombre(nombre_bot)
        
        if datos_bot:
            # 2. Desempaquetamos la tupla según tu estructura de tabla:
            # nombre, token_gemini, token_telegram, explicacion, pdfs (json string), id_almacen
            nombre, t_gemini, t_tele, expl, pdfs_raw, id_almacen = datos_bot
            
            try:
                # 3. Convertimos el string JSON de los PDFs de nuevo a lista de Python
                # Manejamos el caso de que pdfs_raw esté vacío o sea None
                lista_pdfs = json.loads(pdfs_raw) if pdfs_raw else []
                
                # 4. Mandamos a crear el bot en el controlador de bots
                self.controlador_bots.crear_bot(
                    nombre=nombre,
                    token_gemini=t_gemini,
                    token_telegram=t_tele,
                    explicacion=expl,
                    nombres_pdf=lista_pdfs,
                    id_almacen_gemini=id_almacen
                )
                
                print(f"✨ Bot '{nombre}' creado e iniciado con éxito.")
                return True

            except json.JSONDecodeError:
                print(f"❌ Error: El formato de la lista de PDFs para '{nombre_bot}' es inválido.")
            except Exception as e:
                print(f"❌ Error inesperado al crear el bot '{nombre_bot}': {e}")
        else:
            # Ya el print de "No se encontró" lo hace obtener_bot_por_nombre
            print(f"🚫 No se pudo iniciar el bot porque no existe el registro.")
        
        return False
    def crear_almacen_individual(self, nombre_bot):
        """
        Sincroniza y verifica la existencia de un almacén específico en Google Cloud.
        Si no existe en la nube, lo crea y actualiza el ID en la base de datos.
        """
        print(f"\n--- 📦 VERIFICANDO ALMACÉN PARA: {nombre_bot} ---")
        
        # 1. Sincronizamos el estado actual de Google Cloud en el repositorio
        self.controlador_gemini.repositorio.sincronizar_almacenes()
        nombres_en_google = self.controlador_gemini.repositorio.nombres_registrados
        
        # 2. Buscamos los datos del bot en nuestra Base de Datos local
        r = self.db.obtener_bot_por_nombre(nombre_bot)
        
        if not r:
            print(f"❌ Error: El bot '{nombre_bot}' no existe en la base de datos.")
            return None

        # Desempaquetamos (r[0] es nombre, r[5] es id_almacen_gemini)
        id_actual_db = r[5] 
        id_google_real = None

        # 3. VERIFICACIÓN DE COINCIDENCIA CON GOOGLE
        if nombre_bot in nombres_en_google:
            # Si ya existe en la nube, recuperamos su ID técnico
            print(f"✅ El almacén '{nombre_bot}' ya existe en Google Cloud. Saltando creación...")
            id_google_real = self.controlador_gemini.repositorio.obtener_id(nombre_bot)
        else:
            # Si NO existe en la nube, lo creamos mediante la API
            print(f"🆕 Creando nuevo almacén para '{nombre_bot}' en la nube...")
            id_google_real = self.controlador_gemini.repositorio.crear_almacen(nombre_bot)

        # 4. ACTUALIZACIÓN DE LA BASE DE DATOS LOCAL
        if id_google_real:
            if id_actual_db != id_google_real:
                print(f"💾 Guardando nuevo ID en la BD para {nombre_bot}...")
                self.db.actualizar_id_almacen(nombre_bot, id_google_real)
            
            print(f"📡 {nombre_bot} vinculado correctamente al ID: {id_google_real}")
            return id_google_real
        else:
            print(f"❌ Error crítico: No se pudo obtener un ID válido para {nombre_bot}")
            return None
    def subir_pdf_individual(self, nombre_bot):
        """
        Busca los PDFs de un bot específico en la BD y los sube 
        a su almacén de Gemini correspondiente.
        """
        print(f"\n--- 📄 INICIANDO SUBIDA DE PDFS PARA: {nombre_bot} ---")
        
        # 1. Obtenemos el registro específico de la base de datos
        r = self.db.obtener_bot_por_nombre(nombre_bot)

        if not r:
            print(f"❌ Error: El bot '{nombre_bot}' no existe en la base de datos.")
            return

        # Desempaquetamos según tu estructura:
        # r[0] = nombre, r[4] = pdfs (string), r[5] = id_almacen
        string_pdfs = r[4]  
        id_almacen = r[5]

        # 2. Validaciones previas
        if not id_almacen:
            print(f"⏩ Error: {nombre_bot} no tiene un ID de almacén vinculado. Debes crearlo primero.")
            return

        if not string_pdfs or string_pdfs.strip() == "":
            print(f"ℹ️ {nombre_bot} no tiene archivos PDF registrados en la base de datos.")
            return

        # 3. Convertimos el string de la BD ("doc1.pdf, doc2.pdf") en una lista real
        lista_archivos = [p.strip() for p in string_pdfs.split(",") if p.strip()]

        # 4. Sincronización con el Controlador Gemini
        if lista_archivos:
            print(f"🚀 Enviando {len(lista_archivos)} archivos al controlador para el bot: {nombre_bot}...")
            
            # Llamamos a tu función principal del controlador
            self.controlador_gemini.sincronizar_biblioteca(id_almacen, lista_archivos)
            
            print(f"✅ Proceso de subida para {nombre_bot} completado.")
        else:
            print(f"ℹ️ {nombre_bot} tiene el campo PDF vacío tras el procesamiento.")

        print(f"--- ✨ Fin de la tarea para {nombre_bot} ---\n")
    def inicializar_bot_completo(self, nombre_bot):
        """
        Función Maestra: Realiza el flujo completo para un bot específico:
        1. Crea/Verifica el almacén en Google Cloud.
        2. Sube los archivos PDF registrados.
        3. Crea la instancia del bot en memoria.
        """
        print(f"\n{'='*50}")
        print(f"🚀 INICIANDO DESPLIEGE TOTAL: {nombre_bot}")
        print(f"{'='*50}")

        # 1. PASO 1: Gestión del Almacén (Google Cloud)
        # Esta función ya busca en la BD, crea en Google si hace falta y actualiza el ID
        id_almacen = self.crear_almacen_individual(nombre_bot)
        
        if not id_almacen:
            print(f"❌ Abortando: No se pudo obtener un almacén válido para {nombre_bot}.")
            return False

        # 2. PASO 2: Sincronización de Documentos
        # Sube los archivos PDF a ese almacén que acabamos de validar
        try:
            self.subir_pdf_individual(nombre_bot)
        except Exception as e:
            print(f"⚠️ Error durante la subida de PDFs: {e}")
            # Decidimos continuar aunque falle un PDF, por si el almacén ya tenía datos

        # 3. PASO 3: Creación de la Instancia en Memoria
        # Levanta el bot en el controlador de bots con sus tokens y configuración
        exito_memoria = self.crear_bot_individual(nombre_bot)

        if exito_memoria:
            print(f"\n✅ ¡ÉXITO! El bot '{nombre_bot}' está desplegado y operativo.")
            print(f"{'='*50}\n")
            return True
        else:
            print(f"\n❌ Error final: El bot '{nombre_bot}' no se pudo instanciar en memoria.")
            return False
'''

