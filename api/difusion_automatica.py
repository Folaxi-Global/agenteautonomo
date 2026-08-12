import os
import json
import requests
from http.server import BaseHTTPRequestHandler
from supabase import create_client

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 1. Obtener proyecto activo
            supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))
            response = supabase.table("proyectos").select("*").eq("estado", "activo").limit(1).execute()
            
            if not response.data:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'No hay proyectos activos.')
                return

            proyecto = response.data[0]
            subdominio = proyecto['subdominio']

            # 2. Llamada directa al motor de marketing (evitando el fallo de red del host)
            # Usamos la misma lógica para llamar a marketing_viral
            marketing_url = f"https://{self.headers['Host']}/api/marketing_viral?subdominio={subdominio}"
            
            # Aumentamos el timeout a 25 segundos para asegurar que termine la IA
            marketing_resp = requests.get(marketing_url, timeout=25)
            
            if marketing_resp.status_code != 200:
                # DEPURACIÓN: Esto nos dirá exactamente por qué falla
                error_detalles = marketing_resp.text
                raise Exception(f"Falla en marketing_viral (Status {marketing_resp.status_code}): {error_detalles}")
                
            marketing_data = marketing_resp.json().get('campaña', {})

            # 3. Difusión al Webhook
            payload = {
                "nombre_saas": proyecto.get('nombre_proyecto'),
                "url": f"https://{subdominio}.vercel.app",
                "post_content": marketing_data.get('copy_publicacion'),
                "gancho": marketing_data.get('gancho_video_3s')
            }
            requests.post("https://hook.us2.make.com/rerd4mb947e7x33w90r3rk4ijrf6kdq3", json=payload, timeout=10)

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Difusion exitosa.')

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Error detallado: {str(e)}".encode('utf-8'))
