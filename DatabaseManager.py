import sqlite3
import json

class DatabaseManager:
    def __init__(self, db_name="bots_test.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Crea la tabla si no existe, ahora sin tokens."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bots (
                    nombre TEXT PRIMARY KEY,
                    explicacion TEXT,
                    pdfs TEXT,
                    nombre_almacen_gemini TEXT
                )
            ''')
            conn.commit()

    def actualizar_id_almacen(self, nombre_bot, id_google):
        """Actualiza ÚNICAMENTE el ID del almacén."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE bots 
                SET nombre_almacen_gemini = ? 
                WHERE nombre = ?
            ''', (id_google, nombre_bot))
            conn.commit()

    def crear_bot(self, bot):
        """Guarda o actualiza un objeto Bot en la BD (versión sin tokens)."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            pdfs_json = json.dumps(bot.pdfs.obtener_lista_pdf())
            
            cursor.execute('''
                INSERT OR REPLACE INTO bots 
                (nombre, explicacion, pdfs, nombre_almacen_gemini)
                VALUES (?, ?, ?, ?)
            ''', (
                bot.nombre, 
                bot.explicacion, 
                pdfs_json, 
                bot.almacen_gemini # Usamos el nombre del atributo de tu clase Bot
            ))
            conn.commit()

    def cargar_todos(self):
        """Retorna todos los registros de la tabla."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM bots')
            return cursor.fetchall()

    def eliminar_bot(self, nombre):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM bots WHERE nombre = ?', (nombre,))
            conn.commit()

   

def rellenar_db_pruebas(db_name="bots_test.db"):
    # Datos de ejemplo sin tokens
    datos_ejemplo = [
        ("AsistenteLegal", "Experto en leyes.", ["Ley_Autonomia.pdf"], "ALMACEN_LEGAL"),
        ("ChefBot", "Especialista cocina.", ["Recetas.pdf"], "ALMACEN_CHEF"),
        ("SoporteIT", "Soporte técnico.", ["Manual_Redes.pdf"], "ALMACEN_IT"),
        ("BotSeguridad", "Experto en ciberseguridad.", ["Protocolo.pdf"], None)
    ]

    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            # Reiniciamos la tabla para que coincida con el nuevo esquema
            cursor.execute('DROP TABLE IF EXISTS bots')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bots (
                    nombre TEXT PRIMARY KEY,
                    explicacion TEXT,
                    pdfs TEXT,
                    nombre_almacen_gemini TEXT
                )
            ''')

            for nombre, expl, lista_pdfs, n_almacen in datos_ejemplo:
                pdfs_json = json.dumps(lista_pdfs)
                cursor.execute('''
                    INSERT OR REPLACE INTO bots 
                    (nombre, explicacion, pdfs, nombre_almacen_gemini)
                    VALUES (?, ?, ?, ?)
                ''', (nombre, expl, pdfs_json, n_almacen))

            conn.commit()
            print(f"✅ Base de datos '{db_name}' actualizada y limpia de tokens.")

    except sqlite3.Error as e:
        print(f"❌ Error: {e}")

def verificar_datos(db_name="bots_test.db"):
    print("\n--- Contenido actual de la Base de Datos (Esquema Limpio) ---")
    db = DatabaseManager(db_name)
    registros = db.cargar_todos()
    
    for r in registros:
        # r[0]=nombre, r[1]=explicacion, r[2]=pdfs, r[3]=almacen
        lista_pdfs = json.loads(r[2]) 
        print(f"Bot: {r[0]} | Almacén: {r[3]} | PDFs: {len(lista_pdfs)}")

if __name__ == "__main__":
    rellenar_db_pruebas()
    verificar_datos()