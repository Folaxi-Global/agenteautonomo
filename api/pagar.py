import os
import json
import urllib.request
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")  # Tu Token de acceso de Mercado Pago

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)
            subdominio = query_params.get("subdominio", [None])[0]

            if not subdominio:
                self.send_response(400)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                error_res = {"status": "error", "mensaje": "Falta especificar el parámetro 'subdominio'."}
                self.wfile.write(json.dumps(error_res, ensure_ascii=False).encode('utf-8'))
                return

            response = supabase.table("proyectos").select("*").eq("subdominio", subdominio).execute()
            if not response.data:
                self.send_response(404)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                error_res = {"status": "error", "mensaje": f"El proyecto '{subdominio}' no existe."}
                self.wfile.write(json.dumps(error_res, ensure_ascii=False).encode('utf-8'))
                return

            proyecto = response.data[0]
            nombre_proyecto = proyecto.get("nombre_proyecto")
            estado_proyecto = proyecto.get("estado")

            if estado_proyecto != "activo":
                self.send_response(403)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                error_res = {"status": "error", "mensaje": f"El proyecto '{nombre_proyecto}' está inactivo."}
                self.wfile.write(json.dumps(error_res, ensure_ascii=False).encode('utf-8'))
                return

            # Crear preferencia de pago en la API de Mercado Pago dinámicamente
            mp_url = "https://api.mercadopago.com/checkout/preferences"
            payload = {
                "items": [{
                    "title": f"Suscripción a {nombre_proyecto} ({subdominio})",
                    "quantity": 1,
                    "unit_price": 29.00,
                    "currency_id": "USD"
                }],
                "back_urls": {
                    "success": f"https://{subdominio}.vertensglobal.com/gracias",
                    "failure": f"https://{subdominio}.vertensglobal.com/error"
                },
                "auto_return": "approved"
            }

            req_data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(mp_url, data=req_data, headers={
                'Authorization': f'Bearer {MP_ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            })

            with urllib.request.urlopen(req) as resp:
                mp_response = json.loads(resp.read().decode('utf-8'))
                url_checkout_unificado = mp_response.get("init_point")  # Link de pago oficial generado por MP

            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            resultado = {
                "status": "success",
                "pasarela": "Mercado Pago API Pro",
                "proyecto": nombre_proyecto,
                "subdominio": subdominio,
                "url_checkout": url_checkout_unificado,
                "mensaje": f"Preferencia de pago generada con éxito para '{nombre_proyecto}'."
            }
            self.wfile.write(json.dumps(resultado, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            error_res = {"status": "error", "detalles": str(e)}
            self.wfile.write(json.dumps(error_res, ensure_ascii=False).encode('utf-8'))
