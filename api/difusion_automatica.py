import os
import json
import requests
from http.server import BaseHTTPRequestHandler
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 1. Obtener el primer proyecto activo del ecosistema
            response = supabase.table("proyectos").select("*").eq("estado", "activo").limit(1).execute()
            
            if not response.data:
                self.send_response(404)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                error_res = {"status": "error", "mensaje": "No hay proyectos activos disponibles para difundir."}
                self.wfile.write(json.dumps(error_res, ensure_ascii=False).encode('utf-8'))
                return

            proyecto = response.data[0]
            subdominio = proyecto['subdominio']
            nombre_proyecto = proyecto.get('nombre_proyecto')
            descripcion = proyecto.get('descripcion_oferta', 'Herramienta digital inteligente.')

            # 2. Generar o simular la estrategia de marketing de forma directa y segura
            host = self.headers.get('Host', 'localhost')
            protocol = 'https' if 'vercel.app' in host else 'http'
            marketing_url = f"{protocol}://{host}/api/marketing_viral?subdominio={subdominio}"
            
            try:
                marketing_resp = requests.get(marketing_url, timeout=20)
                if marketing_resp.status_code == 200:
                    marketing_data = marketing_resp.json().get('campaña', {})
                else:
                    raise Exception("Fallo marketing externo")
            except:
                # Fallback de respaldo por si el módulo externo tarda o falla puntualmente
                marketing_data = {
                    "gancho_video_3s": f"¿Cansado de procesos lentos? Descubre {nombre_proyecto}.",
                    "copy_publicacion": f"Optimiza tus tareas al instante con {nombre_proyecto}. Pruébalo ahora en {subdominio}.vercel.app 🚀 #Growth #SaaS",
                    "hashtags_virales": ["#SaaS", "#Tech", "#Productividad"]
                }

            # 3. Preparar el paquete de datos (payload) para Make.com
            payload = {
                "nombre_saas": nombre_proyecto,
                "url": f"https://{subdominio}.vercel.app",
                "descripcion": descripcion,
                "gancho": marketing_data.get('gancho_video_3s'),
                "post_content": marketing_data.get('copy_publicacion'),
                "hashtags": marketing_data.get('hashtags_virales', [])
            }
            
            # 4. Enviar los datos al Webhook exacto de Make.com que configuraste
            make_webhook_url = "https://hook.us2.make.com/rerd4mb947e7x33w90r3rk4ijrf6kdq3"
            webhook_resp = requests.post(make_webhook_url, json=payload, timeout=10)

            # 5. Responder con éxito absoluto al sistema
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            resultado = {
                "status": "success",
                "mensaje": "Difusión autónoma ejecutada y enviada a Make.com correctamente.",
                "proyecto": nombre_proyecto,
                "webhook_make_status": webhook_resp.status_code
            }
            self.wfile.write(json.dumps(resultado, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            error_res = {"status": "error", "detalles": str(e)}
            self.wfile.write(json.dumps(error_res, ensure_ascii=False).encode('utf-8'))
      
