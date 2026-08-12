import os
import json
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 1. Consultar todos los proyectos que siguen 'activos'
            response = supabase.table("proyectos").select("*").eq("estado", "activo").execute()
            proyectos = response.data or []
            
            proyectos_evaluados = 0
            proyectos_purgados = 0
            ahora = datetime.now(timezone.utc)

            for proyecto in proyectos:
                proyectos_evaluados += 1
                created_at_str = proyecto.get("created_at")
                
                if not created_at_str:
                    continue
                
                # Parsear la fecha de creación del proyecto en Supabase
                # Reemplazamos la Z por +00:00 para que python la entienda como UTC
                if created_at_str.endswith("Z"):
                    created_at_str = created_at_str[:-1] + "+00:00"
                
                fecha_creacion = datetime.fromisoformat(created_at_str)
                diferencia = ahora - fecha_creacion

                # 2. Si el proyecto lleva 14 días o más operando
                if diferencia >= timedelta(days=14):
                    subdominio = proyecto.get("subdominio")
                    
                    # EJECUTAR KILL-SWITCH: Cambiar estado a purgado o inactivo
                    supabase.table("proyectos").update({
                        "estado": "purgado"
                    }).eq("subdominio", subdominio).execute()
                    
                    proyectos_purgados += 1

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            resultado = {
                "status": "success",
                "mensaje": "Evaluación de ciclos de 14 días ejecutada por el Kill-Switch de A.U.R.A.",
                "proyectos_revisados": proyectos_evaluados,
                "proyectos_purgados": proyectos_purgados
            }
            self.wfile.write(json.dumps(resultado, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "detalles": str(e)}).encode('utf-8'))
