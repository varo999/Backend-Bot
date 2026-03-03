import re
import os

class LimpiadorDatos:
    
    @staticmethod
    def limpiar_nombre_bot(nombre: str) -> str:
        """
        Limpia el nombre del bot para que sea seguro en la DB y Google Gemini.
        - Convierte a minúsculas.
        - Reemplaza espacios por guiones bajos.
        - Elimina caracteres especiales.
        """
        if not nombre:
            return "bot_sin_nombre"
        
        # 1. Minúsculas y quitar espacios en blanco laterales
        nombre = nombre.lower().strip()
        # 2. Reemplazar espacios por guiones bajos
        nombre = nombre.replace(" ", "_")
        # 3. Eliminar todo lo que no sea letras, números o guiones/guiones bajos
        nombre = re.sub(r'[^a-z0-9_-]', '', nombre)
        
        return nombre

    @staticmethod
    def limpiar_explicacion(texto: str) -> str:
        """
        Limpia la descripción o misión del bot.
        - Quita espacios dobles y saltos de línea innecesarios.
        """
        if not texto:
            return ""
        # Une las palabras con un solo espacio, eliminando tabulaciones y saltos de línea
        return " ".join(texto.split())

    @staticmethod
    def limpiar_archivo_raw(archivo_raw) -> str:
        """
        Recibe un objeto de archivo individual (de Django).
        - Extrae el nombre.
        - Lo limpia para evitar errores de sistema de archivos.
        - Asegura la extensión .pdf.
        """
        # 1. Extraer el nombre original del objeto archivo
        nombre_original = archivo_raw.name
        
        # 2. Separar nombre y extensión
        nombre_base, extension = os.path.splitext(nombre_original)
        
        # 3. Limpiar el cuerpo del nombre (reutilizamos la lógica de nombres de bot)
        nombre_limpio = nombre_base.lower().strip().replace(" ", "_")
        nombre_limpio = re.sub(r'[^a-z0-9_-]', '', nombre_limpio)
        
        # 4. Forzar extensión .pdf
        return f"{nombre_limpio}.pdf"