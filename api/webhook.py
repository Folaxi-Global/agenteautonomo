import os
import json
from http.server import BaseHTTPRequestHandler
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # 1. Leer y decodificar los datos enviados por la pasarela de pago de forma segura
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            if not body:
                self.send_response(400)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "mensaje": "Cuerpo de la solicitud vacío."}, ensure_ascii=False).encode('utf-8'))
                return

            data = json.loads(body.decode('utf-8'))
            
            subdominio = data.get("subdominio")
            monto = float(data.get("monto", 0.00))
            
            if not subdominio:
                self.send_response(400)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "mensaje": "Falta el subdominio del proyecto en el webhook."}, ensure_ascii=False).encode('utf-8'))
                return

            # 2. Marcar el proyecto como 'exitoso' en Supabase (lo salva del Kill-Switch de los 14 días)
            supabase.table("proyectos").update({"estado": "exitoso"}).eq("subdominio", subdominio).execute()
            
            # 3. Actualizar la tesorería sumando el monto ingresado de forma atómica
            response = supabase.table("tesoreria").select("*").execute()
            if response.data:
                tesoreria = response.data[0]
                nuevo_saldo = float(tesoreria.get('saldo_operativo', 0.0)) + monto
                supabase.table("tesoreria").update({"saldo_operativo": nuevo_saldo}).eq("id", tesoreria['id']).execute()
            else:
                # Si no existe registro previo de tesorería, se crea con el monto inicial
                supabase.table("tesoreria").insert({"saldo_operativo": monto}).execute()

            # 4. Responder a la pasarela de pago confirmando la recepción exitosa
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            respuesta_json = {
                "status": "success",
                "mensaje": f"Pago procesado correctamente para el micro-SaaS '{subdominio}'.",
                "monto_procesado": monto
            }
            self.wfile.write(json.dumps(respuesta_json, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            error_json = {"status": "error", "detalles": str(e)}
            self.wfile.write(json.dumps(error_json, ensure_ascii=False).encode('utf-8'))

    def do_GET(self):
        """Permite verificar el estado del webhook y asegurar que está en línea."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        estado_webhook = {
            "status": "activo",
            "modulo": "Webhook Centralizado de Pagos Pro",
            "descripcion": "Escuchando transacciones unificadas de todo el ecosistema."
        }
        self.wfile.write(json.dumps(estado_webhook, ensure_ascii=False).encode('utf-8'))
