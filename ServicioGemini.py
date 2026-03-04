from typing import List, Tuple, Callable, Dict, Any, Optional
from google import genai
from google.genai import types
import threading

class ServicioGemini:
    def __init__(self, cliente: genai.Client, chequeo_cliente_func: Callable[[], genai.Client] = None):
        """
        Ahora la clase no guarda un almacén fijo. Se le pasa en cada pregunta.
        """
        self.cliente = cliente
        self.chequeo_cliente = chequeo_cliente_func
        self._lock = threading.Lock()

    def hacer_pregunta(self, pregunta: str, historial: List[Tuple[str, str]], id_almacen: str, modelo: str = "gemini-2.5-flash", top_k: int = 3):
        """
        Realiza una pregunta a Gemini de forma sincronizada (Thread-Safe).
        """
        
        # El 'with self._lock' garantiza que solo un hilo ejecute este bloque a la vez
        with self._lock:
            
            # 1. Asegurar conexión (Punto crítico: evita que dos hilos refresquen a la vez)
            if self.chequeo_cliente:
                try:
                    self.cliente = self.chequeo_cliente()
                except RuntimeError as e:
                    print(f"❌ Error Fatal: No se pudo asegurar ni restaurar la conexión: {e}")
                    return None

            # 2. Validaciones básicas
            if not id_almacen:
                print("❌ Error: No se proporcionó un ID de almacén para realizar la búsqueda RAG.")
                return None

            # 3. Preparar estructura de la conversación
            contents = self._crear_estructura_conversacion(historial, pregunta)
            
            if not contents:
                print("  ❌ La lista 'contents' está vacía.")
                return None

            print(f"\n[DEBUG] Consultando Almacén: {id_almacen}")

            system_instruction = (
                "Eres un bot de consulta interna para personal sanitario. Responde a las preguntas utilizando únicamente la documentación adjunta. "
                "Para cada afirmación que hagas, indica brevemente el nombre del documento o la sección de donde proviene. "
                "Si la información es ambigua o no aparece en los archivos, indica que la base de datos no contiene esa instrucción específica. "
                "Mantén un tono profesional, conciso y estrictamente basado en la evidencia de los PDF."
            )

            # 4. Llamada a la API de Gemini
            try:
                # Importante: Usamos self.cliente que acaba de ser verificado/actualizado arriba
                response = self.cliente.models.generate_content(
                    model=f"models/{modelo}",
                    contents=contents, 
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction, 
                        tools=[
                            types.Tool(
                                file_search=types.FileSearch(
                                    file_search_store_names=[id_almacen],
                                    top_k=top_k
                                )
                            )
                        ],
                        temperature=0.0  # Recomendado para temas sanitarios (evita creatividad/alucinaciones)
                    )
                )

                answer = response.text
                print(f"💬 Respuesta generada usando {id_almacen}")
                return answer

            except Exception as e:
                print(f"❌ Error al hacer la pregunta (API): {e}")
                return None

    def _crear_estructura_conversacion(self, historial: List[Tuple[str, str]], nueva_pregunta: str) -> List[types.Content]:
        conversacion = []
        for pregunta, respuesta in historial:
            conversacion.append(
                types.Content(role="user", parts=[types.Part(text=pregunta)])
            )
            conversacion.append(
                types.Content(role="model", parts=[types.Part(text=respuesta)])
            )
        conversacion.append(
            types.Content(role="user", parts=[types.Part(text=nueva_pregunta)])
        )
        return conversacion
