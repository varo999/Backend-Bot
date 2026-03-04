import sqlite3
import json

class DatabaseManager:
    def __init__(self, db_name="bots_test.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Crea la tabla si no existe, con ID autoincrementable y campo de imagen."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE,
                    explicacion TEXT,
                    pdfs TEXT,
                    nombre_almacen_gemini TEXT,
                    nombre_imagen TEXT
                )
            ''')
            conn.commit()

    def actualizar_id_almacen(self, nombre_bot, id_google):
        """Actualiza ÚNICAMENTE el ID del almacén buscando por nombre."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE bots 
                SET nombre_almacen_gemini = ? 
                WHERE nombre = ?
            ''', (id_google, nombre_bot))
            conn.commit()

    def crear_bot(self, bot):
        """Guarda o actualiza un objeto Bot incluyendo el campo de imagen."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Asumimos que bot.pdfs tiene un método para obtener la lista
            pdfs_json = json.dumps(bot.pdfs.obtener_lista_pdf())
            
            # Usamos INSERT OR REPLACE sobre 'nombre' (que es UNIQUE)
            cursor.execute('''
                INSERT OR REPLACE INTO bots 
                (nombre, explicacion, pdfs, nombre_almacen_gemini, nombre_imagen)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                bot.nombre, 
                bot.explicacion, 
                pdfs_json, 
                bot.almacen_gemini,
                bot.nombre_imagen # Nuevo campo
            ))
            conn.commit()

    def cargar_todos(self):
        """Retorna todos los registros de la tabla."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM bots')
            return cursor.fetchall()

    def eliminar_bot(self, nombre):
        """Elimina un bot por su nombre."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM bots WHERE nombre = ?', (nombre,))
            conn.commit()

def rellenar_db_pruebas(db_name="bots_test.db"):
    # Datos de ejemplo: Nombre, Expl, PDFs, Almacen, Imagen
    datos_ejemplo = [
        ("AsistenteLegal", "Experto en leyes.", ["Ley_Autonomia.pdf"], "ALMACEN_LEGAL", "icon_legal.png"),
        ("ChefBot", "Especialista cocina.", ["Recetas.pdf"], "ALMACEN_CHEF", "icon_chef.png"),
        ("SoporteIT", "Soporte técnico.", ["Manual_Redes.pdf"], "ALMACEN_IT", "icon_it.png"),
        ("BotSeguridad", "Experto en ciberseguridad.", ["Protocolo.pdf"], None, None)
    ]

    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DROP TABLE IF EXISTS bots')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT UNIQUE,
                    explicacion TEXT,
                    pdfs TEXT,
                    nombre_almacen_gemini TEXT,
                    nombre_imagen TEXT
                )
            ''')

            for nombre, expl, lista_pdfs, n_almacen, n_imagen in datos_ejemplo:
                pdfs_json = json.dumps(lista_pdfs)
                cursor.execute('''
                    INSERT INTO bots 
                    (nombre, explicacion, pdfs, nombre_almacen_gemini, nombre_imagen)
                    VALUES (?, ?, ?, ?, ?)
                ''', (nombre, expl, pdfs_json, n_almacen, n_imagen))

            conn.commit()
            print(f"✅ Base de datos '{db_name}' recreada con ID e Imagen.")

    except sqlite3.Error as e:
        print(f"❌ Error: {e}")

def verificar_datos(db_name="bots_test.db"):
    print("\n--- Contenido actual de la Base de Datos (Nuevo Esquema) ---")
    db = DatabaseManager(db_name)
    registros = db.cargar_todos()
    
    for r in registros:
        # r[0]=id, r[1]=nombre, r[2]=explicacion, r[3]=pdfs, r[4]=almacen, r[5]=imagen
        lista_pdfs = json.loads(r[3]) 
        print(f"ID: {r[0]} | Bot: {r[1]} | Imagen: {r[5]} | PDFs: {len(lista_pdfs)}")

if __name__ == "__main__":
    rellenar_db_pruebas()
    verificar_datos()