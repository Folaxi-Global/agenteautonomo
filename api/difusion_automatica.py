import os
import json
import requests
from http.server import BaseHTTPRequestHandler
from supabase import create_client

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Obtener proyecto activo
        supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))
        proyecto = supabase.table("proyectos").select("*").eq("estado", "activo").limit(1).execute().data[0]

        # 2. Obtener estrategia de marketing (llamando a tu propia API)
        marketing_resp = requests.get(f"https://{self.headers['Host']}/api/marketing_viral?subdominio={proyecto['subdominio']}")
        marketing_data = marketing_resp.json()['campaña']

        # 3. Difusión mediante Webhook externo (Make.com/Zapier)
        # Aquí envías el contenido a tu nodo de automatización
        payload = {
            "nombre_saas": proyecto['nombre_proyecto'],
            "url": f"https://{proyecto['subdominio']}.vercel.app",
            "post_content": marketing_data['copy_publicacion'],
            "gancho": marketing_data['gancho_video_3s']
        }
        
        # URL de tu Webhook en Make.com
        requests.post("https://hook.make.com/tu-id-unico-aqui", json=payload)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Difusion iniciada exitosamente.')
