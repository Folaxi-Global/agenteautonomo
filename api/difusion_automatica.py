import os
import json
import requests
from http.server import BaseHTTPRequestHandler
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 1. Inicializar cliente de Supabase y obtener un proyecto activo
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            response = supabase.table("proyectos").select("*").eq("estado", "activo").limit(1).execute()
            
            if not response.data:
                self.send_response(404)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No hay proyectos activos para difundir."}).encode('utf-8'))
                return

            proyecto = response.data[0]
            subdominio = proyecto['subdominio']

            # 2. Obtener estrategia de marketing llamando internamente a tu propia API
            host = self.headers.get('Host', 'localhost')
            protocol = 'https' if 'vercel.app' in host else 'http'
            marketing_url = f"{protocol}://{host}/api/marketing_viral?subdominio={subdominio}"
            
            marketing_resp = requests.get(marketing_url)
            
            if marketing_resp.status_code != 200:
                raise Exception("No se pudo generar la estrategia de marketing para la difusión.")
                
            marketing_data = marketing_resp.json().get('campaña', {})

            # 3. Preparar el payload con los datos listos para Make.com
            payload = {
                "nombre_saas": proyecto.get('nombre_proyecto'),
                "url": f"https://{subdominio}.vercel.app",
                "descripcion": proyecto.get('descripcion_oferta'),
                "gancho": marketing_data.get('gancho_video_3s'),
                "post_content": marketing_data.get('copy_publicacion'),
                "hashtags": marketing_data.get('hashtags_virales', [])
            }
            
            # 4. Enviar los datos al Webhook exacto de Make.com
            make_webhook_url = "https://hook.us2.make.com/rerd4mb947e7x33w90r3rk4ijrf6kdq3"
            webhook_resp = requests.post(make_webhook_url, json=payload)

            # 5. Responder con éxito al sistema
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            resultado = {
                "status": "success",
                "mensaje": "Difusión autónoma ejecutada y enviada a Make.com con éxito.",
                "proyecto": proyecto.get('nombre_proyecto'),
                "webhook_make_status": webhook_resp.status_code
            }
            self.wfile.write(json.dumps(resultado, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            error_res = {"status": "error", "detalles": str(e)}
            self.wfile.write(json.dumps(error_res, ensure_ascii=False).encode('utf-8'))
