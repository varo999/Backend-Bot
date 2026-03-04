class Bot:
    def __init__(self, nombre, explicacion="", pdfs=None, id_almacen_gemini=None, nombre_imagen=None):
        self.nombre = nombre
        self.explicacion = explicacion
        # Inicializa como lista vacía si no se pasan PDFs
        self.pdfs = pdfs if pdfs is not None else [] 
        self.almacen_gemini = id_almacen_gemini
        self.nombre_imagen = nombre_imagen

    def obtener_id_almacen(self):
        return self.almacen_gemini
    
    def __repr__(self):
        return f"<Bot {self.nombre} - {len(self.pdfs)} PDFs>"