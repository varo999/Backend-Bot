from ClaseBot import *
# Asumiendo que la clase Bot está en el mismo archivo o importada
# from Bot import Bot 

class ControladorBots:
    def __init__(self):
        # Usamos un diccionario para buscar bots por nombre fácilmente
        self.diccionario_bots = {}

    def crear_bot(self, nombre, explicacion="", pdfs=None, id_almacen_gemini=None, nombre_imagen=None):
        """Instancia un nuevo Bot y lo añade a la colección (Versión actualizada)."""
        if nombre in self.diccionario_bots:
            print(f"⚠️ El bot '{nombre}' ya existe. Elige un nombre diferente.")
            return None
        
        # 1. Creamos la instancia del Bot
        # Usamos 'pdfs' (lista de strings) y añadimos 'nombre_imagen'
        nuevo_bot = Bot(
            nombre=nombre, 
            explicacion=explicacion, 
            pdfs=pdfs, 
            id_almacen_gemini=id_almacen_gemini,
            nombre_imagen=nombre_imagen
        )
        
        # 2. Lo guardamos en el diccionario en memoria
        self.diccionario_bots[nombre] = nuevo_bot
        
        # 3. Opcional: Si quieres que se guarde automáticamente en la DB al crearlo
        # self.db_manager.crear_bot(nuevo_bot)
        
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

    