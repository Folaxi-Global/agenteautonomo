import os
from google import genai
from google.genai import types

def get_gemini_client():
    """Inicializa y retorna el cliente oficial de Google GenAI."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("La llave de Gemini (GEMINI_API_KEY) no está configurada en el entorno.")
    return genai.Client(api_key=api_key)

def generar_respuesta_estructurada(prompt: str) -> str:
    """Envía un prompt a Gemini utilizando el modelo flash optimizado."""
    client = get_gemini_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    return response.text
