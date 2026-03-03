class GestorPDF:
    def __init__(self, entrada=None):
        """
        Detecta si la entrada es un solo nombre (string) o una lista.
        """
        if entrada is None:
            self.lista = []
        elif isinstance(entrada, list):
            self.lista = entrada
        elif isinstance(entrada, str):
            self.lista = [entrada]  
        else:
            self.lista = []
            print(f"[!] Tipo de dato no soportado: {type(entrada)}. Se inició lista vacía.") 

    def agregar(self, nombre_archivo):
        if nombre_archivo not in self.lista:
            self.lista.append(nombre_archivo)
            return True
        return False

    def quitar(self, nombre_archivo):
        if nombre_archivo in self.lista:
            self.lista.remove(nombre_archivo)
            return True
        return False

    def limpiar(self):
        self.lista = []

    def eliminar_todo(self):
        """Limpia completamente la lista de archivos."""
        self.lista = []
        return True
    
    def obtener_lista_pdf(self):
        """Devuelve la lista actual de PDFs."""
        return self.lista
