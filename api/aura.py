import os
import json
from http.server import BaseHTTPRequestHandler
from google import genai
from google.genai import types
from supabase import create_client, Client

# --- CONFIGURACIÓN CORPORATIVA ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# Inicialización segura
client = genai.Client(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def verificar_tesoreria():
    """Valida el estado financiero actual."""
    try:
        response = supabase.table("tesoreria").select("*").execute()
        return response.data[0] if response.data else {"saldo_operativo": 0.0}
    except Exception:
        return {"saldo_operativo": 0.0, "status": "error_conexion"}

def aura_idear_y_registrar():
    """El cerebro autónomo que define el siguiente activo digital del ecosistema."""
    prompt = (
        "Eres A.U.R.A., un agente autónomo CEO de micro-SaaS. "
        "Genera una idea de micro-servicio web ultra ligero y escalable. "
        "Responde estrictamente en JSON con: 'nombre_proyecto', 'subdominio_sugerido', 'descripcion_oferta'."
    )

    # Llamada al modelo actual y estable
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )
    
    idea_data = json.loads(response.text)

    # Registro atómico en Supabase
    nuevo_proyecto = {
        "nombre_proyecto": idea_data["nombre_proyecto"],
        "subdominio": idea_data["subdominio_sugerido"],
        "descripcion_oferta": idea_data["descripcion_oferta"],
        "estado": "activo"
    }
    
    supabase.table("proyectos").insert(nuevo_proyecto).execute()
    return idea_data

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Ejecución del Ciclo de Vida Autónomo
            tesoreria = verificar_tesoreria()
            proyecto = aura_idear_y_registrar()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            respuesta_json = {
                "status": "success",
                "timestamp": "auto-ejecutado",
                "tesoreria": tesoreria,
                "proyecto_desplegado": proyecto
            }
            self.wfile.write(json.dumps(respuesta_json, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            error_json = {"status": "error", "message": str(e)}
            self.wfile.write(json.dumps(error_json).encode('utf-8'))
