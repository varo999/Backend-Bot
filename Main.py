import time

from Controlador import *
import os
import sys




''' https://www.sanidad.gob.es/organizacion/sns/planCalidadSNS/portada/normativa.htm
Ley 292006, de 26 de julio, de garantías y uso racional de los medicamentos y productos sanitarios.pdf-98 paginas
Ley de medidas sanitarias frente al tabaquismo.pdf - 7paginas
Ley de proteccion de datos de caracter personal.pdf - 12 paginas
Ley General de Sanidad.pdf - 22paginas
Ley de autonomía del paciente y de información y documentación clínica.pdf - 7 paginas '''

'''File Search Store  - 700.000 palabras-1million de token / 
Coste de Indexación: Solo pagas una vez al subirlo.
Precio: 0,15 $ por cada 1.000.000 de tokens (unas 750.000 palabras).
Ejemplo: Si tu PDF tiene 100 páginas (unas 50.000 palabras), indexarlo te costará apenas 0,01 $.'''
"Almacenamiento gratis"
"Gemini 1.5 Flash"
"10 carpetas por clave api gemini"
"1000 paginas por documento o Tamaño máximo: 100 MB por archivo"
"si le pasamos imagenes antes comprimirlas"
"Cloud Run de google cloud solo se paga cuando se utiliza"
"Tráfico moderado (10k - 50k visitas): $10 - $30/mes."
"solo sea contestacion con escritura, el resto sube bastante la tarifa"
'''Entrada (Pregunta + trozo del PDF): 0,075 $ por millón de tokens.
Salida (La respuesta que da el chat): 0,30 $ por millón de tokens.
"base de datos entre 12-18e en google cloud
En dinero real: Una conversación típica donde el usuario hace una pregunta y la IA responde usando tus PDFs cuesta aproximadamente 0,0005 $. Es decir, con 1 dólar podrías responder unas 2.000 preguntas.'''
import time
import os
import io

# Simulador de objeto archivo de Django para pruebas
class MockArchivoDjango:
    def __init__(self, nombre, contenido_bytes):
        self.name = nombre
        self.filename = nombre # Para que el limpiador lo reconozca
        self.contenido = contenido_bytes
    
    def chunks(self):
        # Simula el generador de trozos de Django
        yield self.contenido

if __name__ == "__main__":
    print("🚀 Iniciando Controlador para pruebas de registro...")
    
    controlador = None
    
    try:
        controlador = Controlador(
            api_key=CLAVE_API, 
            token=BOT_TOKEN
        )

        # --- PRUEBA DE REGISTRO DE NUEVO BOT ---
        print("\n🧪 Simulando registro de un nuevo bot...")
        
        # 1. Creamos "archivos" ficticios en memoria
        foto_prueba = MockArchivoDjango("Mi Foto Bot.jpg", b"datos_de_imagen_ficticios")
        pdf_prueba = MockArchivoDjango("Manual Instrucciones.pdf", b"datos_de_pdf_ficticios")
        
        # 2. Llamamos a tu nueva función
        # Nota: lista_pdfs_django debe ser una lista []
        resultado = controlador.registrar_y_desplegar_nuevo_bot(
            nombre_usuario="Bot de Prueba 01",
            explicacion_usuario="Este es un bot creado desde el main para testear la DB y las carpetas.",
            lista_pdfs_django=[pdf_prueba],
            imagen_django=foto_prueba
        )

        if resultado:
            print(f"✅ Prueba exitosa: {resultado}")
        else:
            print("⚠️ El bot se registró pero el despliegue no devolvió resultado.")

        # --- MANTENER VIVO ---
        print("\nSistemas activos. Presiona Ctrl+C para salir.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nCerrando el bot y limpiando recursos...")
    except Exception as e:
        print(f"❌ Error fatal al iniciar el sistema: {e}")