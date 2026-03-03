from typing import List, Optional
from ConexionGemini import *
from AlmacenGemini import *
from ServicioGemini import *
from SubirArchivoAlmacen import *
import os

CLAVE_API = "AIzaSyB7EtBwf0oG5vgNTx2S2U-HoWVQOjWgrxc"

class ControladorGemini:
    
    def __init__(self, clave_api: str):
        """Inicializa las tres capas de la aplicación."""

        self.conexion: ConexionGemini = ConexionGemini(clave_api=clave_api)
        self.cliente_gemini = self.conexion.obtener_cliente()
        self.repositorio: AlmacenGemini= AlmacenGemini(cliente=self.cliente_gemini)
        self.sincronizador = SubirArchivoAlmacen(genai_client=self.cliente_gemini,  ruta_documentos="/Documentos")
        self.servicio = ServicioGemini(cliente=self.cliente_gemini,chequeo_cliente_func=self.conexion.obtener_cliente)

        
        print("Controlador Gemini listo. Capas inicializadas.")
        
    def obtener_cliente_gemini(self):
            """
            Devuelve el cliente de Gemini. 
            Si es None, intenta recuperarlo delegando a la capa de Conexión.
            """
            self.cliente_gemini = self.conexion.obtener_cliente()
            
            return self.cliente_gemini

    def crear_almacen(self, nombre_bot: str) -> str:
        """
        Este es el método principal que usará tu clase Controlador (la de Telegram).
        Le pasas el nombre del Bot y te devuelve el ID real de Google para guardarlo en la DB.
        """
        # Delegamos la responsabilidad al repositorio que ya sabe verificar duplicados
        id_google = self.repositorio.crear_almacen(nombre_bot)
        
        return id_google

    def eliminar_almacen_busqueda(self, nombre_bot: str):
        return self.repositorio.eliminar_almacen_busqueda(nombre_bot)

    def hacer_pregunta(self, pregunta: str, historial: List[Tuple[str, str]], id_almacen: str) -> Optional[str]:
        """
        Intermediario: Recibe la pregunta, el historial y el ID del almacén 
        y los delega directamente al ServicioGemini.
        """
        # Delegamos al servicio pasando el id_almacen que recibimos por parámetro
        respuesta = self.servicio.hacer_pregunta(
            pregunta=pregunta, 
            historial=historial,
            id_almacen=id_almacen  # <-- Lo pasamos tal cual llega
        )
        
        return respuesta
    
    def limpiar_todo_el_proyecto(self):
        self.repositorio.limpiar_todo_el_proyecto()
        print("todo borrado")
    
    def sincronizar_biblioteca(self, id_almacen, lista_pdfs_db):
        """
        Orquesta la subida de archivos desde la DB al almacén de Gemini.
        """
        return self.sincronizador.ejecutar_sincronizacion(id_almacen, lista_pdfs_db)
