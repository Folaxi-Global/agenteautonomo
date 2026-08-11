
import os
import json
from http.server import BaseHTTPRequestHandler
from google import genai
from google.genai import types
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)

def generar_codigo_sitio(nombre_proyecto, descripcion):
    """Usa Gemini para generar el contenido HTML/CSS del micro-sitio basado en la idea."""
    prompt = (
        f"Eres un desarrollador experto en frontend. Crea una página web estática ultra ligera en un solo archivo HTML (con CSS incluido) "
        f"para el siguiente micro-servicio digital:\n"
        f"Nombre del Proyecto: {nombre_proyecto}\n"
        f"Descripción: {descripcion}\n"
        f"El diseño debe ser moderno, limpio, responsivo, enfocado en conversión y con un botón de pago simulado. "
        f"Devuelve estrictamente el código HTML limpio, sin bloques de texto markdown adicionales ni explicaciones."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    
    return response.text

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Leer los datos enviados en la petición (ej. el proyecto a desplegar)
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            nombre_proyecto = data.get("nombre_proyecto")
            subdominio = data.get("subdominio")
            descripcion = data.get("descripcion_oferta", "Herramienta digital automatizada.")

            if not nombre_proyecto or not subdominio:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Faltan datos requeridos (nombre_proyecto o subdominio)"}).encode('utf-8'))
                return

            # 1. Generar el código de la landing page con Gemini
            html_generado = generar_codigo_sitio(nombre_proyecto, descripcion)

            # 2. Registrar o actualizar el estado del despliegue en Supabase
            supabase.table("proyectos").update({
                "estado": "activo"
            }).eq("subdominio", subdominio).execute()

            # Responder con éxito y el HTML generado
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            respuesta = {
                "status": "success",
                "mensaje": f"Micro-sitio para '{nombre_proyecto}' generado con éxito.",
                "subdominio": f"{subdominio}.tu-dominio.com",
                "html_preview": html_generado[:200] + "..." # Muestra un extracto del código
            }
            self.wfile.write(json.dumps(respuesta).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "detalles": str(e)}).encode('utf-8'))
