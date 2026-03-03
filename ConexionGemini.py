from typing import List, Tuple
from google import genai
from google.genai.errors import APIError
import os
import glob
from google.genai import types

class ConexionGemini:
    
    def __init__(self, clave_api: str):
    
        self.clave_api = clave_api
        self.client = None
        self._inicializar_cliente()
        print("Cliente de Gemini inicializado.")

    def _inicializar_cliente(self):
        """Intenta inicializar el cliente de Gemini y maneja errores."""
        if self.client is not None:
            return
        if self.clave_api is None or self.clave_api == "":
            print("ADVERTENCIA: Clave API no proporcionada. No se puede inicializar el cliente.")
            return
        try:
            self.client = genai.Client(api_key=self.clave_api)
            print("✅ Cliente de Gemini inicializado correctamente.")
        except Exception as e:
            print(f"❌ ERROR: Fallo al inicializar el cliente: {e}")
            self.client = None

    def obtener_cliente(self):
        """Devuelve el cliente de Gemini inicializado."""
        if self.client is None:
            print("ℹ️ Cliente no inicializado. Intentando inicializar en el getter...")
            self._inicializar_cliente()
            raise RuntimeError("El cliente de Gemini no está inicializado. Verifique la clave API.")
        return self.client       