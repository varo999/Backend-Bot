import sqlite3
import json

import sqlite3

class DatabaseManager:
    def __init__(self, db_name="bots_test.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Crea las tablas de bots, conversaciones y mensajes si no existen."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Activar el soporte para claves foráneas en SQLite
            cursor.execute('PRAGMA foreign_keys = ON;')

            # 1. Tabla de Bots (Existente)
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

            # 2. Tabla de Conversaciones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversaciones (
                    id_conversacion INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_usuario TEXT, -- Aquí puedes guardar el ID del usuario de tu sistema
                    id_bot INTEGER,
                    titulo TEXT,
                    fecha_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (id_bot) REFERENCES bots(id) ON DELETE CASCADE
                )
            ''')

            # 3. Tabla de Mensajes
            # Dentro de init_db, actualiza la creación de la tabla mensajes:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mensajes (
                    id_mensaje INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_conversacion INTEGER,
                    rol TEXT, -- 'usuario' o 'asistente'
                    contenido TEXT,
                    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (id_conversacion) REFERENCES conversaciones(id_conversacion) ON DELETE CASCADE
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

    def añadir_mensaje(self, id_conversacion, rol, contenido):
        """Método genérico para insertar mensajes."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO mensajes (id_conversacion, rol, contenido)
                    VALUES (?, ?, ?)
                ''', (id_conversacion, rol, contenido))
                conn.commit()
                return cursor.lastrowid # Devuelve el ID del mensaje creado
        except sqlite3.Error as e:
            print(f"Error al añadir mensaje: {e}")
            return None

    def añadir_pregunta(self, id_conversacion, texto_pregunta):
        """Registra la pregunta del usuario."""
        return self.añadir_mensaje(id_conversacion, "usuario", texto_pregunta)

    def añadir_respuesta(self, id_conversacion, texto_respuesta):
        """Registra la respuesta generada por el Bot."""
        return self.añadir_mensaje(id_conversacion, "asistente", texto_respuesta)
    
    def obtener_historial_chat(self, id_conv):
        """Recupera el historial con el rol para poder formatearlo."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # IMPORTANTE: Seleccionamos contenido Y rol
            cursor.execute('''
                SELECT contenido, fecha, rol 
                FROM mensajes 
                WHERE id_conversacion = ? 
                ORDER BY fecha ASC
            ''', (id_conv,))
            return cursor.fetchall()

    def obtener_id_bot_por_nombre(self, nombre_bot):
        """Devuelve el ID numérico de un bot buscando por su nombre."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM bots WHERE nombre = ?', (nombre_bot,))
            resultado = cursor.fetchone()
            return resultado[0] if resultado else None

    def crear_nueva_conversacion(self, id_bot, id_usuario="usuario_anonimo", titulo="Nueva Conversación"):
        """Inserta una nueva conversación y devuelve su ID."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversaciones (id_usuario, id_bot, titulo)
                VALUES (?, ?, ?)
            ''', (id_usuario, id_bot, titulo))
            conn.commit()
            return cursor.lastrowid


def rellenar_db_pruebas(db_name="bots_test.db"):
    # 1. Datos de ejemplo para BOTS
    bots_ejemplo = [
        ("AsistenteLegal", "Experto en leyes.", ["Ley_Autonomia.pdf"], "ALMACEN_LEGAL", "icon_legal.png"),
        ("ChefBot", "Especialista cocina.", ["Recetas.pdf"], "ALMACEN_CHEF", "icon_chef.png"),
        ("SoporteIT", "Soporte técnico.", ["Manual_Redes.pdf"], "ALMACEN_IT", "icon_it.png"),
        ("BotSeguridad", "Experto en ciberseguridad.", ["Protocolo.pdf"], None, None)
    ]

    try:
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            
            # Limpiamos todo
            cursor.execute('DROP TABLE IF EXISTS mensajes')
            cursor.execute('DROP TABLE IF EXISTS conversaciones')
            cursor.execute('DROP TABLE IF EXISTS bots')

            # Re-creamos las tablas
            cursor.execute('''CREATE TABLE bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE, explicacion TEXT, pdfs TEXT, 
                nombre_almacen_gemini TEXT, nombre_imagen TEXT)''')

            cursor.execute('''CREATE TABLE conversaciones (
                id_conversacion INTEGER PRIMARY KEY AUTOINCREMENT,
                id_usuario TEXT, id_bot INTEGER, titulo TEXT,
                fecha_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_bot) REFERENCES bots(id) ON DELETE CASCADE)''')

            # --- FIJATE AQUÍ: Añadimos la columna 'rol' ---
            cursor.execute('''CREATE TABLE mensajes (
                id_mensaje INTEGER PRIMARY KEY AUTOINCREMENT,
                id_conversacion INTEGER, 
                rol TEXT, 
                contenido TEXT,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_conversacion) REFERENCES conversaciones(id_conversacion) ON DELETE CASCADE)''')

            # 2. Insertar BOTS
            for nombre, expl, lista_pdfs, n_almacen, n_imagen in bots_ejemplo:
                pdfs_json = json.dumps(lista_pdfs)
                cursor.execute('''
                    INSERT INTO bots (nombre, explicacion, pdfs, nombre_almacen_gemini, nombre_imagen)
                    VALUES (?, ?, ?, ?, ?)
                ''', (nombre, expl, pdfs_json, n_almacen, n_imagen))

            # 3. Insertar CONVERSACIONES
            cursor.execute("INSERT INTO conversaciones (id_usuario, id_bot, titulo) VALUES (?, ?, ?)", 
                           ("user_123", 1, "Consulta sobre Contratos"))
            id_conv_1 = cursor.lastrowid
            
            cursor.execute("INSERT INTO conversaciones (id_usuario, id_bot, titulo) VALUES (?, ?, ?)", 
                           ("user_123", 2, "Cena de Navidad"))
            id_conv_2 = cursor.lastrowid

            # --- FIJATE AQUÍ: Insertamos 3 valores incluyendo el ROL ---
            mensajes_ejemplo = [
                (id_conv_1, "usuario", "Hola, ¿puedes revisar este contrato?"),
                (id_conv_1, "asistente", "Claro, analizando las cláusulas legales..."),
                (id_conv_2, "usuario", "¿Cómo se hace un pavo relleno?"),
                (id_conv_2, "asistente", "Para un pavo jugoso, necesitas marinarlo 24 horas.")
            ]
            cursor.executemany("INSERT INTO mensajes (id_conversacion, rol, contenido) VALUES (?, ?, ?)", mensajes_ejemplo)

            conn.commit()
            print(f"✅ Base de datos '{db_name}' recreada CORRECTAMENTE con columna 'rol'.")

    except sqlite3.Error as e:
        print(f"❌ Error: {e}")

def verificar_datos(db_name="bots_test.db"):
    print("\n--- Estado de la Base de Datos ---")
    with sqlite3.connect(db_name) as conn:
        cursor = conn.cursor()
        
        # Verificar Bots
        cursor.execute("SELECT id, nombre FROM bots")
        print("\n[BOTS]:", cursor.fetchall())
        
        # Verificar Conversaciones y Mensajes unidos
        cursor.execute('''
            SELECT c.titulo, b.nombre, m.contenido 
            FROM mensajes m
            JOIN conversaciones c ON m.id_conversacion = c.id_conversacion
            JOIN bots b ON c.id_bot = b.id
        ''')
        print("\n[HISTORIAL DE CHATS]:")
        for fila in cursor.fetchall():
            print(f"Chat: '{fila[0]}' ({fila[1]}) -> {fila[2]}")

if __name__ == "__main__":
    rellenar_db_pruebas()
    verificar_datos()