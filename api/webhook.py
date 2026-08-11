
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
            # Leer los datos que envía la pasarela de pago
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            subdominio = data.get("subdominio")
            monto = float(data.get("monto", 0.00))
            
            if not subdominio:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Falta el subdominio del proyecto en el webhook"}).encode('utf-8'))
                return

            # 1. Marcar el proyecto como exitoso en Supabase
            supabase.table("proyectos").update({"estado": "exitoso"}).eq("subdominio", subdominio).execute()
            
            # 2. Actualizar la tesorería sumando el monto ingresado
            response = supabase.table("tesoreria").select("*").execute()
            if response.data:
                tesoreria = response.data[0]
                nuevo_saldo = float(tesoreria.get('saldo_operativo', 0)) + monto
                supabase.table("tesoreria").update({"saldo_operativo": nuevo_saldo}).eq("id", tesoreria['id']).execute()
            else:
                # Si no existe registro previo de tesorería, se crea con el monto inicial
                supabase.table("tesoreria").insert({"saldo_operativo": monto}).execute()

            # Responder a la pasarela de pago confirmando la recepción
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            respuesta_json = {
                "status": "success",
                "mensaje": f"Pago registrado para el subdominio '{subdominio}'.",
                "monto_procesado": monto
            }
            self.wfile.write(json.dumps(respuesta_json).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_json = {"status": "error", "detalles": str(e)}
            self.wfile.write(json.dumps(error_json).encode('utf-8'))
