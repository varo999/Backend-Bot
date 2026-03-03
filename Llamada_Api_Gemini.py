'''
HAY QUE SEPARAR LO QUE SON LAS CONEXIONES CON LAS FUNCIONES, INCLUSO 
LAS DISTINTAS APIS,
DONDE CREAMOS EL BOT DE TELEGRAM UTILIZA POLLING, QUE SIGNIFICA QUE TODO EL RATO
ESTA ESCUCHANDO, POR ESTE MOTIVO LO HEMOS PUESTO EN UNA MAQUINA VIRTUAL.
'''

from typing import List, Tuple
from google import genai
from google.genai.errors import APIError
import os
import glob
from google.genai import types

class Llamada_Api_Gemini:
    
    def __init__(self, clave_api: str, controlador):
    
        self.clave_api = clave_api
        self.client = None
        self.almacen_archivos = None    
        self.controlador = controlador   
        self.archivos_subidos = []       
        
        self._inicializar_cliente()
        
        print("Cliente de Gemini inicializado.")


    def crear_almacen_busqueda(self, nombre_almacen: str):
        if self.almacen_archivos:
            print(f"El almacén ya está configurado con ID: {self.almacen_archivos.name}")
            return self.almacen_archivos

        print(f"Creando FileSearchStore: '{nombre_almacen}'...")
        try:
            self.almacen_archivos = self.client.file_search_stores.create(
                config={'display_name': nombre_almacen}
            )
            print(f"✅ Almacén creado. ID: {self.almacen_archivos.name}")
            return self.almacen_archivos
        except APIError as e:
            print(f"❌ Error al crear el almacén: {e}")
            return None

    def obtener_rutas_carpeta(self, ruta_carpeta: str, extensiones: List[str] = ['.pdf', '.txt', '.docx']):
        """
        Busca archivos con las extensiones especificadas dentro de una carpeta.
        Devuelve una lista de rutas de archivo.
        """
        if not os.path.isdir(ruta_carpeta):
            print(f"❌ Error: La ruta '{ruta_carpeta}' no es una carpeta válida.")
            return []

        rutas_archivos = []
        
        for ext in extensiones:
            patron_busqueda = os.path.join(ruta_carpeta, f'*{ext}')
            rutas_archivos.extend(glob.glob(patron_busqueda))
            
        return rutas_archivos

    def subir_carpeta(self, ruta_carpeta = "./Documentos"):
        """
        Centraliza la lógica para subir todos los archivos soportados de una carpeta.
        """
        print(f"\n--- Procesando carpeta: {ruta_carpeta} ---")
        
        
        lista_rutas = self.obtener_rutas_carpeta(ruta_carpeta)
        
        if not lista_rutas:
            print("⚠️ No se encontraron archivos soportados en la carpeta.")
            return []
        
        print(f"✅ Encontrados {len(lista_rutas)} archivos para indexar.")
        
        
        return self.subir_e_indexar_archivos(rutas_archivos=lista_rutas)

    def subir_e_indexar_archivos(self, rutas_archivos: list[str]):
        """
        Sube e indexa una lista de archivos al FileSearchStore existente.
        """
        if not self.almacen_archivos:
            print("❌ Error: No hay FileSearchStore configurado.")
            return []

        archivos_indexados = []
        nombre_almacen = self.almacen_archivos.name
        
        
        for ruta_archivo in rutas_archivos:
            
            if not os.path.exists(ruta_archivo):
                print(f"❌ Error: Archivo no encontrado en la ruta: {ruta_archivo}. Saltando...")
                continue 
                
            nombre_archivo = os.path.basename(ruta_archivo)
            print(f"Cargando archivo '{nombre_archivo}'...")

            try:
                uploaded_file = self.client.file_search_stores.upload_to_file_search_store(
                    file_search_store_name=nombre_almacen,
                    file=ruta_archivo,
                    config={'display_name': nombre_archivo}
                )

                self.archivos_subidos.append(uploaded_file.name)
                archivos_indexados.append(uploaded_file)
                print(f"✅ Archivo indexado correctamente. ID: {uploaded_file.name}")

            except APIError as e:
                print(f"❌ Error al subir e indexar {nombre_archivo}: {e}")        
        return archivos_indexados

    def eliminar_almacen_busqueda(self):
        if not self.almacen_archivos:
            print("No hay almacén configurado para eliminar.")
            return

        nombre_almacen = self.almacen_archivos.name

        try:
            print(f"Borrando almacén: {nombre_almacen} con force=True...")
            self.client.file_search_stores.delete(
                name=nombre_almacen,
                config={'force': True}
            )
            self.almacen_archivos = None
            self.archivos_subidos = []
            print(f"✅ Almacén '{nombre_almacen}' eliminado correctamente.")
        except APIError as e:
            print(f"❌ Error al eliminar el almacén: {e}")

    def iniciar_rag(self, nombre_almacen: str, ruta_carpeta: str = "./Documentos"):
    
        print("\n=== 🚀 INICIANDO PREPARACIÓN RAG ===")
        
        # 1. Crear el FileSearchStore
        almacen = self.crear_almacen_busqueda(nombre_almacen=nombre_almacen)
        
        if not almacen:
            print("🛑 Fallo en la preparación: No se pudo crear el almacén.")
            return False
            
        # 2. Subir e indexar la carpeta
        archivos_indexados = self.subir_carpeta(ruta_carpeta=ruta_carpeta)
        
        if archivos_indexados:
            print(f"=== ✅ RAG LISTO: {len(archivos_indexados)} archivos indexados. ===\n")
            return True
        else:
            print("=== ⚠️ RAG INACTIVO: No se subieron archivos al almacén. ===\n")
            return False

    def hacer_pregunta(self, pregunta: str, historial: List[Tuple[str, str]], modelo: str = "gemini-2.5-flash", top_k: int = 3):
        """
        Realiza una pregunta a Gemini, utilizando el historial de conversación 
        y la herramienta FileSearch para RAG, restringiendo la respuesta solo a los documentos.
        """
        if self._inicializar_cliente():
            print("❌ Error Fatal: No se pudo asegurar ni restaurar la conexión con Gemini.")
            return None

        if not self.almacen_archivos:
            print("❌ Error: No hay FileSearchStore configurado para hacer preguntas.")
            return None

        nombre_almacen = self.almacen_archivos.name
        
       
        print(f"\n[DEBUG 1] Historial recibido (Tipo: {type(historial)}, Longitud: {len(historial)}):")
        print(historial)
        
        contents = self._crear_estructura_conversacion(historial, pregunta)
        
       
        print(f"[DEBUG 2] Contenido a enviar a Gemini (Longitud: {len(contents)}):")
        if contents:
            
            try:
                print(f"  Último Rol: {contents[-1].role}, Texto: {contents[-1].parts[0].text[:80]}...") 
            except Exception:
                print("  El formato del objeto Content puede ser incorrecto o estar vacío.")
        else:
            print("  ❌ La lista 'contents' está vacía. ¡Revisa _crear_estructura_conversacion!")
       
        system_instruction = (
            "Eres un asistente de búsqueda de documentos. Tu única fuente de información "
            "para responder a las preguntas es el contenido que se te proporciona "
            "a través de la herramienta File Search. Si no puedes encontrar la respuesta "
            "en los documentos, debes responder claramente: 'No pude encontrar la respuesta "
            "en los documentos proporcionados'."
        )
        # ---------------------------------------------
        
        try:
            response = self.client.models.generate_content(
                model=f"models/{modelo}",
                contents=contents, 
                config=types.GenerateContentConfig(
                    # Agregamos la instrucción del sistema
                    system_instruction=system_instruction, 
                    tools=[
                        types.Tool(
                            file_search=types.FileSearch(
                                file_search_store_names=[nombre_almacen],
                                top_k=top_k
                            )
                        )
                    ]
                )
            )

            answer = response.text
            print("\n💬 Respuesta de Gemini:")
            print(answer)
            return answer

        except Exception as e:
            # --- DEBUG 3: Captura de Error de la API (IMPORTANTE) ---
            print(f"❌ Error al hacer la pregunta (API): {e}")
            # --------------------------------------------------------
            return None

    def _crear_estructura_conversacion(self, historial: List[Tuple[str, str]], nueva_pregunta: str) -> List[types.Content]:
        """
        Convierte el historial de tuplas (pregunta, respuesta) en el formato
        List[Content] que espera la API de Gemini (alternando 'user' y 'model'),
        usando la sintaxis del constructor directo para evitar errores.
        """
        conversacion = []
        
        # 1. Añadir el historial previo
        for pregunta, respuesta in historial:
            # Turno del usuario
            conversacion.append(
                types.Content(role="user", parts=[types.Part(text=pregunta)]) # <--- ¡CAMBIO AQUÍ!
            )
            # Turno del modelo (respuesta previa)
            conversacion.append(
                types.Content(role="model", parts=[types.Part(text=respuesta)])  # <--- ¡CAMBIO AQUÍ!
            )
            
        # 2. Añadir la pregunta actual del usuario
        conversacion.append(
            types.Content(role="user", parts=[types.Part(text=nueva_pregunta)]) # <--- ¡CAMBIO AQUÍ!
        )
        
        return conversacion

    def _inicializar_cliente(self):
        """Intenta inicializar el cliente de Gemini y maneja errores."""
        
        # 🎯 NUEVO: Si self.client ya está inicializado, sale de la función inmediatamente.
        if self.client is not None:
            # Opcional: Puedes añadir un print si quieres ver que se omitió la inicialización
            # print("ℹ️ Cliente de Gemini ya existe. Omitiendo la inicialización.")
            return

        # El resto del código solo se ejecuta si self.client era None.
        if self.clave_api is None or self.clave_api == "":
            print("ADVERTENCIA: Clave API no proporcionada. No se puede inicializar el cliente.")
            return

        try:
            self.client = genai.Client(api_key=self.clave_api)
            print("✅ Cliente de Gemini inicializado correctamente.")
        except Exception as e:
            print(f"❌ ERROR: Fallo al inicializar el cliente: {e}")
            self.client = None
