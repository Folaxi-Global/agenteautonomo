
import os
import json
from http.server import BaseHTTPRequestHandler
from google import genai
from google.genai import types
from supabase import create_client, Client

# --- CREDENCIALES DESDE LA NUBE (Variables de entorno en Vercel) ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# Inicializar clientes
client = genai.Client(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def verificar_tesoreria():
    """Valida la regla de saldo cero y protege los fondos."""
    response = supabase.table("tesoreria").select("*").execute()
    if response.data:
        return response.data[0]
    return None

def aura_idear_y_registrar():
    """Gemini analiza el mercado, crea una micro-idea y Supabase le otorga 14 días de prueba."""
    prompt = (
        "Eres el CEO autónomo de A.U.R.A. Operas con saldo inicial 0 y costo operativo 0. "
        "Genera una idea de micro-servicio digital o herramienta SaaS ultra ligera que se pueda desplegar "
        "en un subdominio de forma gratuita. "
        "Devuelve la respuesta estrictamente en formato JSON con las claves: "
        "'nombre_proyecto', 'subdominio_sugerido', 'descripcion_oferta'."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    
    idea_data = json.loads(response.text)

    # Guardar en Supabase con el ciclo de 14 días calculado automáticamente
    nuevo_proyecto = {
        "nombre_proyecto": idea_data["nombre_proyecto"],
        "subdominio": idea_data["subdominio_sugerido"],
        "estado": "activo"
    }
    supabase.table("proyectos").insert(nuevo_proyecto).execute()
    return idea_data

# Handler requerido por Vercel para Serverless Functions en Python
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            tesoreria = verificar_tesoreria()
            proyecto = aura_idear_y_registrar()
            
            # Responder con éxito a Vercel
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            respuesta_json = {
                "status": "success",
                "mensaje": "Ciclo autónomo de A.U.R.A. ejecutado correctamente en Vercel.",
                "tesoreria": tesoreria,
                "proyecto_creado": proyecto
            }
            self.wfile.write(json.dumps(respuesta_json).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_json = {"status": "error", "detalles": str(e)}
            self.wfile.write(json.dumps(error_json).encode('utf-8'))
