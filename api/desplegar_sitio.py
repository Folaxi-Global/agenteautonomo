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

def generar_codigo_sitio_pro(nombre_proyecto, descripcion):
    """Utiliza Gemini para generar una landing page estática profesional basada en la idea del agente."""
    prompt = (
        f"Eres un desarrollador experto en frontend y conversión SaaS. Crea una página web estática ultra ligera en un solo archivo HTML "
        f"(con CSS moderno y responsivo integrado) para el siguiente micro-servicio digital:\n"
        f"Nombre del Proyecto: {nombre_proyecto}\n"
        f"Descripción: {descripcion}\n"
        f"El diseño debe ser estilo futurista/neón (fondo oscuro, tarjetas estilizadas, botones de llamada a la acción claros y sección de precios). "
        f"Devuelve estrictamente el código HTML limpio, sin bloques de texto markdown adicionales ni explicaciones previas."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    
    return response.text

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            nombre_proyecto = data.get("nombre_proyecto")
            subdominio = data.get("subdominio")
            descripcion = data.get("descripcion_oferta", "Micro-servicio automatizado por IA.")

            if not nombre_proyecto or not subdominio:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Faltan datos requeridos (nombre_proyecto o subdominio)"}).encode('utf-8'))
                return

            # 1. Generar la landing page con IA
            html_generado = generar_codigo_sitio_pro(nombre_proyecto, descripcion)

            # 2. Actualizar el estado del proyecto en Supabase a 'activo'
            supabase.table("proyectos").update({
                "estado": "activo"
            }).eq("subdominio", subdominio).execute()

            # Responder con éxito
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            respuesta = {
                "status": "success",
                "mensaje": f"Micro-sitio para '{nombre_proyecto}' desplegado y generado con éxito.",
                "subdominio": f"{subdominio}.vercel.app",
                "preview_html": html_generado[:150] + "..."
            }
            self.wfile.write(json.dumps(respuesta).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "detalles": str(e)}).encode('utf-8'))
