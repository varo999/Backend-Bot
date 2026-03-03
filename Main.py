import time

from Controlador import *
import os
import sys


CLAVE_API = "AIzaSyB7EtBwf0oG5vgNTx2S2U-HoWVQOjWgrxc"
BOT_TOKEN = "8563315952:AAGkAGPWVvaY_NpdNGWyeH3tDIDE1cFwQQI"
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

# Clase auxiliar para engañar al sistema y simular archivos de Django
class SimulatedFile:
    def __init__(self, name, content):
        self.name = name
        self.content = content
    def chunks(self):
        yield self.content

if __name__ == "__main__":
    print("🚀 Iniciando Controlador y Bot de Telegram...")
    
    try:
        controlador = Controlador(api_key=CLAVE_API, token=BOT_TOKEN)
        
        # --- PASO 1: VER ESTADO INICIAL ---
        print("\n📊 ESTADO INICIAL:")
        print(f"Bots en Memoria: {list(controlador.controlador_bots.diccionario_bots.keys())}")
        print(f"Bots en Telegram: {controlador.bot_telegram.lista_bots}")
        
        print("\n🔔 ACCIÓN: Ve a Telegram y usa /start para ver la lista actual.")
        input("👉 Presiona ENTER cuando estés listo para añadir el nuevo bot...")

        # --- PASO 2: SIMULAR NUEVO BOT ---
        print("\n🆕 Registrando 'Bot_Entrenamiento'...")
        
        # Simulamos un PDF (puedes poner uno real que tengas en la carpeta si quieres)
        archivo_simulado = SimulatedFile("manual_usuario.pdf", b"Contenido de prueba para Gemini")
        
        controlador.registrar_y_desplegar_nuevo_bot(
            nombre_usuario="Bot_Consulta",
            explicacion_usuario="Soy un bot experto en manuales de usuario.",
            lista_pdfs_django=[archivo_simulado]
        )

        # --- PASO 3: VERIFICAR CAMBIOS ---
        print("\n✨ REGISTRO COMPLETADO ✨")
        print(f"Nueva lista en Memoria: {list(controlador.controlador_bots.diccionario_bots.keys())}")
        print(f"Nueva lista en Telegram: {controlador.bot_telegram.lista_bots}")
        
        print("\n🔔 ACCIÓN: ¡Vuelve a Telegram y usa /start! El nuevo bot ya debería aparecer.")
        
        # Mantener vivo el proceso
        print("\nSistemas activos. Presiona Ctrl+C para salir.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nCerrando el bot y limpiando recursos...")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()