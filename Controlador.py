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

