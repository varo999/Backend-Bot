from ClaseBot import *
# Asumiendo que la clase Bot está en el mismo archivo o importada
# from Bot import Bot 

class ControladorBots:
    def __init__(self):
        # Usamos un diccionario para buscar bots por nombre fácilmente
        self.diccionario_bots = {}

    def crear_bot(self, nombre, explicacion="", nombres_pdf=None, id_almacen_gemini=None):
        """Instancia un nuevo Bot y lo añade a la colección (Versión Limpia)."""
        if nombre in self.diccionario_bots:
            print(f"⚠️ El bot '{nombre}' ya existe. Elige un nombre diferente.")
            return None
        
        # 1. Creamos la instancia del Bot (Llamada coherente con la nueva clase Bot)
        # Eliminamos: token_gemini y token_telegram de la llamada
        nuevo_bot = Bot(
            nombre=nombre, 
            explicacion=explicacion, 
            nombres_pdf=nombres_pdf, 
            id_almacen_gemini=id_almacen_gemini
        )
        
        # 2. Lo guardamos en nuestro "almacén"
        self.diccionario_bots[nombre] = nuevo_bot
        print(f"🤖 Bot '{nombre}' creado y registrado con éxito.")
        
        return nuevo_bot

    def eliminar_bot(self, nombre):
        """Elimina un bot de la gestión."""
        if nombre in self.diccionario_bots:
            del self.diccionario_bots[nombre]
            print(f"🗑️ Bot '{nombre}' eliminado.")
            return True
        print(f"❌ No se encontró el bot '{nombre}'.")
        return False

    def obtener_bot(self, nombre):
        """Busca y retorna una instancia de Bot específica."""
        return self.diccionario_bots.get(nombre)

    def obtener_id_almacen_por_nombre(self, nombre_bot: str) -> str:
        """
        Busca un bot por su nombre y devuelve su id_almacen_gemini.
        Si no existe, devuelve None.
        """
        # 1. Buscamos el objeto bot en el diccionario
        bot = self.diccionario_bots.get(nombre_bot)
        
        # 2. Si el bot existe, llamamos a su método interno para obtener el ID
        if bot:
            # Importante: Asegúrate de que en la clase Bot el atributo se llame 
            # igual que lo que devuelve su método (id_almacen_gemini o alamcen_gemini)
            return bot.obtener_id_almacen()
        
        print(f"❌ Error: No se encontró ningún bot con el nombre '{nombre_bot}'")
        return None

    