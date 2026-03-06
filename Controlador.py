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
        self.ruta_img = self.crear_carpeta_imagenes()
        self.ruta_doc = self.crear_carpeta_pdf()
        self.limpiador = LimpiadorDatos()
        
        # 2. Motores (Gemini y DB)
        self.controlador_gemini = ControladorGemini(clave_api=api_key,ruta_documentos=self.ruta_doc)
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

    def crear_carpeta_imagenes(self):
        """Crea la carpeta 'imagenes' si no existe y devuelve su ruta absoluta."""
        raiz = os.path.dirname(os.path.abspath(__file__))
        ruta_imagenes = os.path.join(raiz, "imagenes")
        
        # exist_ok=True evita errores si la carpeta ya existe
        os.makedirs(ruta_imagenes, exist_ok=True)
        
        return ruta_imagenes

    def crear_carpeta_pdf(self):
        """Crea la carpeta 'pdf' si no existe y devuelve su ruta absoluta."""
        raiz = os.path.dirname(os.path.abspath(__file__))
        ruta_pdf = os.path.join(raiz, "pdf")
        
        # exist_ok=True evita errores si la carpeta ya existe
        os.makedirs(ruta_pdf, exist_ok=True)
        
        return ruta_pdf

    def _procesar_despliegue_bot(self, registro):
        """
        Método privado que contiene la lógica central de despliegue.
        Recibe una tupla de la DB: (id, nombre, expl, pdfs, almacen, imagen)
        """
        # 1. Desempaquetado consistente con el esquema de 6 columnas
        # Usamos "_" para ignorar el ID de la base de datos (r[0])
        _, nombre, expl, pdfs_raw, id_almacen_db, nombre_imagen = registro
        
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

        # 3. Lógica de PDFs (ahora es una lista de strings pura)
        lista_pdfs = []
        if pdfs_raw:
            try:
                lista_pdfs = json.loads(pdfs_raw)
            except Exception as e:
                print(f"⚠️ Error al decodificar PDFs de {nombre}: {e}")
                lista_pdfs = []

        # Sincronización de archivos si hay PDFs y almacén
        if lista_pdfs and id_almacen_db:
            self.controlador_gemini.sincronizar_biblioteca(id_almacen_db, lista_pdfs)

        # 4. Creación de Instancia en Memoria
        # Pasamos 'pdfs' y 'nombre_imagen' para que coincida con tu clase Bot
        return self.controlador_bots.crear_bot(
            nombre=nombre,
            explicacion=expl,
            pdfs=lista_pdfs,
            id_almacen_gemini=id_almacen_db,
            nombre_imagen=nombre_imagen
        )

    def inicializar_todos_los_bots(self):
        """Carga y despliega todos los bots de la base de datos."""
        registros = self.db.cargar_todos()
        if not registros:
            print("⚠️ No hay bots para procesar.")
            return

        for r in registros:
            # Nuevo mapeo tras añadir ID:
            # r[0] = id, r[1] = nombre, r[2] = explicacion, r[3] = pdfs_json, etc.
            nombre_bot = r[1] 
            
            try:
                # Enviamos la fila completa al procesador
                self._procesar_despliegue_bot(r)
            except Exception as e:
                print(f"❌ Error procesando bot '{nombre_bot}' (ID: {r[0]}): {e}")
        
        print(f"✨ Proceso masivo finalizado. {len(registros)} bots procesados.") 

    def registrar_y_desplegar_nuevo_bot(self, nombre_usuario, explicacion_usuario, lista_pdfs_django, imagen_django):
        """
        Registra un bot, guarda sus PDFs e Imagen limpiando los nombres y lo despliega.
        """
        # --- PASO 1: LIMPIEZA ---
        nombre_limpio = self.limpiador.limpiar_nombre_bot(nombre_usuario)
        explicacion_limpia = self.limpiador.limpiar_explicacion(explicacion_usuario)
        
        # --- PASO 2: GUARDADO FÍSICO DE LA IMAGEN ---
        nombre_imagen_limpio = None
        if imagen_django:
            try:
                # Limpiamos el nombre usando tu función específica para imágenes
                nombre_imagen_limpio = self.limpiador.limpiar_nombre_imagen(imagen_django)
                ruta_imagen_final = os.path.join(self.ruta_img, nombre_imagen_limpio)
                
                # Guardar físicamente en la carpeta de imágenes
                with open(ruta_imagen_final, 'wb+') as destino:
                    for chunk in imagen_django.chunks():
                        destino.write(chunk)
                print(f"🖼️ Imagen guardada: {nombre_imagen_limpio}")
            except Exception as e:
                print(f"❌ Error guardando imagen: {e}")

        # --- PASO 3: GUARDADO FÍSICO DE PDFs ---
        nombres_pdfs_finales = []
        for archivo_pdf in lista_pdfs_django:
            try:
                nombre_archivo_limpio = self.limpiador.limpiar_archivo_raw(archivo_pdf)
                ruta_pdf_final = os.path.join(self.ruta_doc, nombre_archivo_limpio)
                
                # Guardar físicamente
                with open(ruta_pdf_final, 'wb+') as destino:
                    for chunk in archivo_pdf.chunks():
                        destino.write(chunk)
                
                nombres_pdfs_finales.append(nombre_archivo_limpio)
            except Exception as e:
                print(f"❌ Error guardando PDF {archivo_pdf.name}: {e}")

        # --- PASO 4: INSERTAR EN BASE DE DATOS ---
        pdfs_json = json.dumps(nombres_pdfs_finales)
        
        with sqlite3.connect(self.db.db_name) as conn:
            cursor = conn.cursor()
            # Actualizamos para incluir la columna nombre_imagen
            cursor.execute('''
                INSERT OR REPLACE INTO bots (nombre, explicacion, pdfs, nombre_almacen_gemini, nombre_imagen)
                VALUES (?, ?, ?, ?, ?)
            ''', (nombre_limpio, explicacion_limpia, pdfs_json, None, nombre_imagen_limpio))
            conn.commit()

        print(f"✅ Bot '{nombre_limpio}' guardado en DB con imagen '{nombre_imagen_limpio}'.")

        # --- PASO 5: DESPLIEGUE ---
        # Actualizamos el registro para que el despliegue también sepa de la imagen si es necesario
        registro_para_despliegue = (
            None,
            nombre_limpio, 
            explicacion_limpia, 
            pdfs_json, 
            None,
            nombre_imagen_limpio
        )
        
        resultado = self._procesar_despliegue_bot(registro_para_despliegue)

        # --- PASO 6: ACTUALIZACIÓN DE TELEGRAM ---
        if hasattr(self, 'bot_telegram') and self.bot_telegram:
            self.bot_telegram.actualizar_lista_desde_controlador()
            print(f"📲 Menú de Telegram actualizado.")

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

    def procesar_consulta_bot(self, nombre_bot: str, pregunta: str, id_conversacion: int) -> str:
        """
        Procesa la consulta cargando el historial de la BD y guardando la nueva interacción.
        """
        # 1. Verificación de existencia del bot
        if nombre_bot not in self.controlador_bots.diccionario_bots:
            print(f"❌ Error: El bot '{nombre_bot}' no está registrado.")
            return "Lo siento, el asistente seleccionado no es válido."

        # 2. Obtener ID del almacén
        id_almacen = self.controlador_bots.obtener_id_almacen_por_nombre(nombre_bot)
        if not id_almacen:
            return "Lo siento, este asistente no tiene acceso a sus documentos ahora mismo."

        # --- NUEVA LÓGICA DE BASE DE DATOS ---
        
        # 3. Cargar historial de la base de datos
        # Asumimos que self.db es tu DatabaseManager
        mensajes_db = self.db.obtener_historial_chat(id_conversacion) 
        
        # 4. Formatear historial para Gemini: List[Tuple[user_msg, bot_msg]]
        # Como los mensajes vienen en filas individuales, agrupamos pares (Pregunta, Respuesta)
        historial_formateado: List[Tuple[str, str]] = []
        
        # El historial_chat devuelve (contenido, fecha, rol) según lo configurado antes
        # Aquí un truco para emparejar pregunta del usuario con respuesta del bot:
        temp_pregunta = None
        for msg in mensajes_db:
            # Usamos desempaquetado seguro para evitar el IndexError
            # msg[0] = contenido, msg[1] = fecha, msg[2] = rol
            try:
                contenido = msg[0]
                rol = msg[2]
                
                if rol == "usuario":
                    temp_pregunta = contenido
                elif rol == "asistente" and temp_pregunta:
                    historial_formateado.append((temp_pregunta, contenido))
                    temp_pregunta = None
            except IndexError:
                print("⚠️ Advertencia: Un mensaje en la BD no tiene el formato esperado.")
                continue

        # 5. LLAMADA AL CONTROLADOR GEMINI
        respuesta = self.controlador_gemini.hacer_pregunta(
            pregunta=pregunta,
            historial=historial_formateado,
            id_almacen=id_almacen
        )

        # 6. GUARDAR EN BASE DE DATOS
        if respuesta:
            # Guardamos la pregunta del usuario
            self.db.añadir_pregunta(id_conversacion, pregunta)
            # Guardamos la respuesta del bot
            self.db.añadir_respuesta(id_conversacion, respuesta)
            return respuesta
        else:
            return "No he podido encontrar información relacionada en los documentos."

    def guardar_conversacion(self, nombre_bot: str, id_usuario: str = "user_default") -> int:
        """
        Crea una nueva conversación en la base de datos para un bot específico
        y devuelve el ID de la conversación generada.
        """
        # 1. Buscamos el ID del bot por su nombre
        id_bot = self.db.obtener_id_bot_por_nombre(nombre_bot)
        
        if id_bot is None:
            print(f"❌ Error: No se encontró el bot '{nombre_bot}' en la base de datos.")
            return None

        # 2. Definimos un título sencillo
        titulo_chat = f"Chat con {nombre_bot}"

        # 3. Creamos la conversación en la BD
        id_nueva_conv = self.db.crear_nueva_conversacion(
            id_bot=id_bot, 
            id_usuario=id_usuario, 
            titulo=titulo_chat
        )

        if id_nueva_conv:
            print(f"✅ Nueva conversación creada (ID: {id_nueva_conv}) para el bot {nombre_bot}.")
            return id_nueva_conv
        else:
            print("❌ Error al crear la conversación en la base de datos.")
            return None

