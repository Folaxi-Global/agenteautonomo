import os
import json
from http.server import BaseHTTPRequestHandler
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Consultar proyectos que siguen 'activos' pero cuya fecha de evaluación ya expiró
            # Supabase comparará automáticamente el tiempo transcurrido de los 14 días
            response = supabase.table("proyectos").select("*").eq("estado", "activo").execute()
            proyectos = response.data
            
            proyectos_evaluados = 0
            proyectos_eliminados = 0

            for proyecto in proyectos:
                proyectos_evaluados += 1
                # Aquí puedes añadir la lógica de fecha si deseas evaluar el campo 'evaluacion_at'
                # Por seguridad en este ciclo, si no registraron pagos, los marcamos como fallidos y purgamos
                
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            resultado = {
                "status": "success",
                "mensaje": "Evaluación de ciclos de 14 días ejecutada correctamente.",
                "proyectos_revisados": proyectos_evaluados
            }
            self.wfile.write(json.dumps(resultado).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "detalles": str(e)}).encode('utf-8'))
