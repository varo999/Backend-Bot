from GestorPDF import *
class Bot:
    def __init__(self, nombre, explicacion="", nombres_pdf=None, id_almacen_gemini=None):
        # Eliminamos token_gemini y token_telegram de los parámetros y del self
        self.nombre = nombre
        self.explicacion = explicacion
        self.pdfs = GestorPDF(nombres_pdf)
        self.almacen_gemini = id_almacen_gemini

        
    def obtener_id_almacen(self):
        # También corrige el retorno aquí:
        return self.almacen_gemini
