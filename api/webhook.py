import os
import json
import mercadopago # Usaremos la librería para verificar el evento
from http.server import BaseHTTPRequestHandler
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")
MP_WEBHOOK_SECRET = os.environ.get("MP_WEBHOOK_SECRET") # Opcional: Tu clave secreta del webhook de MP para seguridad

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
mp = mercadopago.SDK(MP_ACCESS_TOKEN)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # 1. Leer el cuerpo de la notificación (payload) enviada por Mercado Pago
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.wfile.read(content_length)
            json_payload = json.loads(post_data.decode('utf-8'))

            # 2. Opcional: Validar que la petición viene de MP (seguridad)
            # En producción, se recomienda verificar la firma del header 'X-Signature'
            # signature = self.headers.get('X-Signature')
            # if not mp.webhook().validate(json_payload, signature):
            #     self.send_response(401)
            #     self.end_headers()
            #     return

            # 3. Procesar el evento de Mercado Pago
            # Los eventos comunes son 'payment' (pago individual) o 'merchant_order' (orden)
            # La API de Orders que configuramos suele usar 'merchant_order'
            topic = json_payload.get("topic") # Ej: 'payment', 'merchant_order'
            resource_id = json_payload.get("data", {}).get("id") # Ej: ID del pago

            # Imprimir para debug en Vercel logs
            print(f"Recibiendo notificación MP. Topic: {topic}, ID: {resource_id}")

            if topic == "payment":
                # Obtener detalles completos del pago usando la SDK
                payment_info = mp.payment().get(resource_id)
                payment_data = payment_info["response"]

                # --- LÓGICA DE ACTIVACIÓN EN SUPABASE ---
                # Extraer el subdominio que guardamos en 'external_reference' en el paso 1
                subdominio_asociado = payment_data.get("external_reference")
                estado_pago = payment_data.get("status") # Ej: 'approved', 'rejected', 'pending'
                id_transaccion_mp = payment_data.get("id")

                if estado_pago == "approved":
                    # Actualizar la tabla proyectos en Supabase
                    supabase.table("proyectos").update({
                        "estado": "activo", # Cambiamos a activo
                        "fecha_activacion": "now()",
                        "id_pago_mp": str(id_transaccion_mp), # Guardamos el ID de MP para referencia
                        "estado_pago_mp": estado_pago
                    }).eq("subdominio", subdominio_asociado).execute()

                    print(f"✅ AUTOMATIZACIÓN MP: Proyecto '{subdominio_asociado}' activado tras pago exitoso.")
                    self.send_response(200)
                    self.end_headers()
                    return

                elif estado_pago == "rejected":
                    # Opcional: Actualizar estado a rechazado
                    supabase.table("proyectos").update({
                        "estado": "pago_rechazado",
                        "estado_pago_mp": estado_pago
                    }).eq("subdominio", subdominio_asociado).execute()
                    print(f"❌ AUTOMATIZACIÓN MP: Pago rechazado para '{subdominio_asociado}'.")
                    self.send_response(200)
                    self.end_headers()
                    return

            elif topic == "merchant_order":
                 # Similar lógica pero para órdenes, si tu integración genera órdenes
                 print(f"Procesando orden comercial ID: {resource_id}")
                 # ... lógica para obtener la orden, buscar el pago asociado y activar ...
                 self.send_response(200)
                 self.end_headers()
                 return

            else:
                # Evento no manejado o de prueba
                print(f"Evento MP recibido no manejado. Topic: {topic}")
                self.send_response(200)
                self.end_headers()
                return

        except Exception as e:
            # Enviar respuesta de error si algo sale mal
            self.send_response(500)
            print(f"Error en webhook MP: {str(e)}")
            self.end_headers()
