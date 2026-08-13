import os
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 1. Capturar el subdominio del micro-SaaS que solicita el cobro
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)
            subdominio = query_params.get("subdominio", [None])[0]

            if not subdominio:
                self.send_response(400)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                error_res = {"status": "error", "mensaje": "Falta especificar el parámetro 'subdominio' del proyecto a cobrar."}
                self.wfile.write(json.dumps(error_res, ensure_ascii=False).encode('utf-8'))
                return

            # 2. Verificar existencia del proyecto en Supabase de forma atómica
            response = supabase.table("proyectos").select("*").eq("subdominio", subdominio).execute()
            if not response.data:
                self.send_response(404)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                error_res = {"status": "error", "mensaje": f"El proyecto '{subdominio}' no existe en el ecosistema."}
                self.wfile.write(json.dumps(error_res, ensure_ascii=False).encode('utf-8'))
                return

            proyecto = response.data[0]
            nombre_proyecto = proyecto.get("nombre_proyecto")
            estado_proyecto = proyecto.get("estado")

            # Validar que el proyecto esté activo para cobrar
            if estado_proyecto != "activo":
                self.send_response(403)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                error_res = {"status": "error", "mensaje": f"El proyecto '{nombre_proyecto}' se encuentra inactivo o purgado."}
                self.wfile.write(json.dumps(error_res, ensure_ascii=False).encode('utf-8'))
                return

            # 3. Construcción del flujo centralizado de pago unificado
            url_checkout_unificado = f"https://link.mercadopago.cl/tupagoautorizado?ref={subdominio}" 

            # 4. Responder con éxito detallado (Ideal para APIs frontend o WebViews)
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            resultado = {
                "status": "success",
                "pasarela": "Vía de Pago Centralizada Pro",
                "proyecto": nombre_proyecto,
                "subdominio": subdominio,
                "url_checkout": url_checkout_unificado,
                "mensaje": f"Canal de pago unificado abierto exitosamente para '{nombre_proyecto}'."
            }
            self.wfile.write(json.dumps(resultado, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            error_res = {"status": "error", "detalles": str(e)}
            self.wfile.write(json.dumps(error_res, ensure_ascii=False).encode('utf-8'))
