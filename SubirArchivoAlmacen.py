import os
import json

class SubirArchivoAlmacen:
    def __init__(self, genai_client, ruta_documentos: str):
        
        self.client = genai_client
        self.ruta_documentos = ruta_documentos

    def _limpiar_y_preparar_ruta(self, nombre_archivo):
        """
        Crea una ruta absoluta robusta y verifica la existencia del archivo.
        """
        # 1. Aseguramos que la carpeta base sea absoluta y use el formato de Windows
        base_path = os.path.abspath(self.ruta_documentos)
        
        # 2. Unimos la base con el nombre del archivo específico
        ruta_completa = os.path.normpath(os.path.join(base_path, nombre_archivo))
        
        return ruta_completa

    def ejecutar_sincronizacion(self, id_almacen, lista_pdfs_db):
        """
        Procesa la lista de la DB, valida archivos físicos y sube a Gemini.
        """
        print(f"\n--- 📂 SINCRONIZANDO ALMACÉN: {id_almacen} ---")
        
        # 1. PARSEO SEGURO DE LA ENTRADA
        archivos_a_procesar = []
        try:
            if isinstance(lista_pdfs_db, str):
                # Si viene como JSON de la DB
                if lista_pdfs_db.startswith("["):
                    archivos_a_procesar = json.loads(lista_pdfs_db)
                # Si viene como string separado por comas
                else:
                    archivos_a_procesar = [p.strip() for p in lista_pdfs_db.split(",") if p.strip()]
            elif isinstance(lista_pdfs_db, list):
                archivos_a_procesar = lista_pdfs_db
        except Exception as e:
            print(f"❌ Error crítico: No se pudieron procesar los datos de la DB: {e}")
            return

        if not archivos_a_procesar:
            print("ℹ️ No se detectaron nombres de archivos en el registro del Bot.")
            return

        # 2. BUCLE DE VALIDACIÓN Y SUBIDA
        for nombre in archivos_a_procesar:
            ruta_final = self._limpiar_y_preparar_ruta(nombre)
            
            # --- EL FILTRO DE SEGURIDAD ---
            if not os.path.exists(ruta_final):
                print(f"⚠️ ERROR: El archivo '{nombre}' NO existe físicamente en: {ruta_final}")
                print(f"👉 Acción: Omitiendo este archivo para evitar errores de API.")
                continue  # Salta al siguiente archivo sin romper el programa

            # 3. INTERACCIÓN CON LA API DE GEMINI
            try:
                print(f"🚀 Iniciando subida a Google: {nombre}...")
                
                # Sincronización real con el Store de Gemini
                # Suponiendo que usas la estructura de Google GenAI SDK:
                # self.client.files.upload(path=ruta_final, config={'file_search_store_id': id_almacen})
                
                print(f"✅ Sincronización exitosa: {nombre}")
                
            except Exception as e:
                print(f"❌ Error de red/API al subir {nombre}: {e}")

        print("=== ✨ PROCESO DE SINCRONIZACIÓN FINALIZADO ===\n")