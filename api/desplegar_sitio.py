import os
import json
from http.server import BaseHTTPRequestHandler
from google import genai
from google.genai import types
from supabase import create_client, Client

# --- CONFIGURACIÓN DE ENTORNO ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generar_codigo_sitio_pro(nombre_proyecto, descripcion):
    """Utiliza Gemini 2.0 para generar una landing page estática profesional y autónoma."""
    prompt = (
        f"Eres un desarrollador experto en frontend y conversión SaaS. Crea una página web estática ultra ligera en un solo archivo HTML "
        f"(con CSS moderno, responsivo y diseño ciber-neón integrado) para el siguiente micro-servicio digital:\n"
        f"Nombre del Proyecto: {nombre_proyecto}\n"
        f"Descripción: {descripcion}\n"
        f"Devuelve estrictamente el código HTML limpio. No incluyas explicaciones previas."
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    
    html_limpio = response.text.strip()
    # Limpiar bloques de markdown si la IA los incluye por error
    if html_limpio.startswith("```html"):
        html_limpio = html_limpio[7:]
    if html_limpio.startswith("```"):
        html_limpio = html_limpio[3:]
    if html_limpio.endswith("```"):
        html_limpio = html_limpio[:-3]
        
    return html_limpio.strip()

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
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Faltan datos requeridos (nombre_proyecto o subdominio)"}).encode('utf-8'))
                return

            # 1. Generar la landing page con IA
            html_generado = generar_codigo_sitio_pro(nombre_proyecto, descripcion)

            # 2. Actualizar el estado del proyecto en Supabase a 'activo'
            supabase.table("proyectos").update({
                "estado": "activo",
                "descripcion_oferta": descripcion
            }).eq("subdominio", subdominio).execute()

            # 3. Respuesta exitosa
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            respuesta = {
                "status": "success",
                "mensaje": f"Micro-sitio para '{nombre_proyecto}' desplegado de forma autónoma.",
                "subdominio": f"{subdominio}.vercel.app",
                "preview_html": html_generado[:150] + "..."
            }
            self.wfile.write(json.dumps(respuesta, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "detalles": str(e)}).encode('utf-8'))

    def do_GET(self):
        """Permite verificar el estado del endpoint o disparar una prueba rápida por GET."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "activo", "modulo": "desplegar_sitio.py Pro"}).encode('utf-8'))
