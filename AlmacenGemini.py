from typing import List, Optional, Tuple
from google import genai
from google.genai.errors import APIError
import os
import glob
from google.genai import types

class AlmacenGemini:
    def __init__(self, cliente: genai.Client):
        self.cliente = cliente
        # Nuestra única fuente de verdad en memoria para los IDs
        self.mapeo_almacenes = {} 
        #self.sincronizar_almacenes()
        print("✅ RepositorioAlmacen inicializado (Modo Diccionario).")

    def sincronizar_almacenes(self):
        """Consulta Google y actualiza el diccionario de mapeo."""
        try:
            remotos = list(self.cliente.file_search_stores.list())
            
            # 🔄 Reconstruimos el mapeo: {display_name: name}
            self.mapeo_almacenes = {a.display_name: a.name for a in remotos}
            
            return self.mapeo_almacenes
        except Exception as e:
            print(f"❌ Error al sincronizar con Google: {e}")
            return {}
    @property
    def nombres_registrados(self) -> list:
        return list(self.mapeo_almacenes.keys())

    def crear_almacen(self, nombre_bot: str) -> str:
        """
        Confía en el mapeo actual. Solo llama a la API si el bot no existe en memoria.
        """
        # --- 1. YA NO LLAMAMOS A sincronizar_almacenes() AQUÍ ---

        # 2. Búsqueda directa en memoria (O(1) - instantáneo)
        if nombre_bot in self.mapeo_almacenes:
            return self.mapeo_almacenes[nombre_bot]

        # 3. Solo si no está en el mapa, procedemos a la creación física
        print(f"🆕 El almacén '{nombre_bot}' no está en el mapa local. Creando en Google...")
        try:
            nuevo_almacen = self.cliente.file_search_stores.create(
                config={'display_name': nombre_bot}
            )
            
            # 4. Actualizamos el mapeo para que la próxima consulta sea instantánea
            id_google = nuevo_almacen.name
            self.mapeo_almacenes[nombre_bot] = id_google
            
            print(f"✅ Creado con éxito. ID: {id_google}")
            return id_google

        except Exception as e:
            print(f"❌ Error al crear almacén para {nombre_bot}: {e}")
            return ""

    def obtener_id(self, nombre_bot: str) -> str:
        """Acceso directo al ID sin lógica de creación."""
        return self.mapeo_almacenes.get(nombre_bot, "")

    def eliminar_almacen_busqueda(self, nombre_bot: str) -> bool:
        """
        Elimina un almacén en Google Gemini usando el nombre del bot.
        También lo elimina de la fuente de verdad (mapeo_almacenes).
        """
        # 1. Obtener el ID de Google (name) a partir del nombre del bot (display_name)
        id_google = self.obtener_id(nombre_bot)

        if not id_google:
            print(f"⚠️ No se puede eliminar: '{nombre_bot}' no existe en el mapa local.")
            return False

        try:
            print(f"🗑️ Borrando en Google: {nombre_bot} (ID: {id_google}) con force=True...")
            
            # 2. Llamada a la API para borrar físicamente en Google
            # 'force': True elimina el almacén aunque tenga archivos dentro
            self.cliente.file_search_stores.delete(
                name=id_google,
                config={'force': True}
            )

            # 3. Eliminar del diccionario (fuente de verdad en memoria)
            del self.mapeo_almacenes[nombre_bot]
            
            print(f"✅ Almacén '{nombre_bot}' eliminado correctamente de Google y del diccionario.")
            return True

        except APIError as e:
            print(f"❌ Error de API al eliminar el almacén {nombre_bot}: {e}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado al eliminar {nombre_bot}: {e}")
            return False
    