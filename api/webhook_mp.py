import os
import json
import hmac
import hashlib
import requests
import mercadopago
from http.server import BaseHTTPRequestHandler
from supabase import create_client, Client

# --- CONFIGURACIÓN DE SEGURIDAD Y AMBIENTE ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")
MP_WEBHOOK_SECRET = os.environ.get("MP_WEBHOOK_SECRET")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
FROM_EMAIL = "onboarding@vartens.com"

# --- INICIALIZACIÓN DE CLIENTES ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
mp = mercadopago.SDK(MP_ACCESS_TOKEN)


def provisionar_servicio(subdominio, email_cliente):
    """Entrega efectiva del servicio y envío de credenciales mediante Resend."""
    print(f"🚀 Iniciando provisión del servicio para '{subdominio}' a '{email_cliente}'...")
    try:
        res = supabase.table("proyectos").select("*").eq("subdominio", subdominio).execute()
        if not res.data:
            print(f"❌ Error de provisión: Proyecto {subdominio} no encontrado en DB.")
            return

        proyecto = res.data[0]
        nombre_sitio = proyecto.get("nombre_proyecto", "Tu Nuevo SaaS")
        url_acceso = f"https://{subdominio}.vartens.com"

        asunto = f"¡Bienvenido a {nombre_sitio}! Tu acceso ya está activo."
        cuerpo_email = f"""
        ¡Hola!
        ¡Gracias por tu suscripción a {nombre_sitio}! Te confirmamos que tu pago ha sido procesado con éxito.
        Tu servicio ya está activo y listo para usar. Datos de acceso:
        🌐 URL de tu sitio: <a href='{url_acceso}'>{url_acceso}</a>
        👤 Usuario: {email_cliente}
        Atentamente,
        El equipo de Vartens
        """

        headers = {
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        }
        email_payload = {
            "from": FROM_EMAIL,
            "to": email_cliente,
            "subject": asunto,
            "html": cuerpo_email
        }

        response = requests.post("https://api.resend.com/emails", headers=headers, json=email_payload)
        if response.status_code == 200:
            print(f"✅ Email de provisión enviado exitosamente a '{email_cliente}'.")
            supabase.table("proyectos").update({"email_onboarding_enviado": True}).eq("subdominio", subdominio).execute()
        else:
            print(f"❌ Error al enviar email vía Resend: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error crítico durante la provisión: {str(e)}")


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # 1. Leer headers y cuerpo de la petición
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.wfile.read(content_length)
            json_payload = json.loads(post_data.decode('utf-8'))

            # 2. Validación opcional pero recomendada de firma x-signature de Mercado Pago
            x_signature = self.headers.get('x-signature')
            x_request_id = self.headers.get('x-request-id')
            
            if MP_WEBHOOK_SECRET and x_signature and x_request_id:
                try:
                    ts_part = x_signature.split(';')[0]
                    v1_part = x_signature.split(';')[1]
                    timestamp = ts_part.split(':')[1]
                    expected_hash = v1_part.split(':')[1]
                    
                    resource_id = json_payload.get('data', {}).get('id')
                    if resource_id:
                        manifest = f"id:{resource_id};request-id:{x_request_id};ts:{timestamp};"
                        calculated_hash = hmac.new(
                            MP_WEBHOOK_SECRET.encode('utf-8'),
                            manifest.encode('utf-8'),
                            hashlib.sha256
                        ).hexdigest()
                        
                        if not hmac.compare_digest(calculated_hash, expected_hash):
                            print("⚠️ Advertencia: Firma de Webhook de MP no coincide exactamente.")
                except Exception as ex:
                    print(f"⚠️ Error validando firma digital (continuando de todas formas): {str(ex)}")

            # 3. Procesar evento de Mercado Pago
            topic = json_payload.get("topic", json_payload.get("type"))
            resource_id = json_payload.get("data", {}).get("id")

            print(f"Recibiendo notificación MP. Topic: {topic}, ID: {resource_id}")

            if topic == "payment" and resource_id:
                payment_info = mp.payment().get(resource_id)
                payment_data = payment_info.get("response", {})

                subdominio_asociado = payment_data.get("external_reference")
                estado_pago = payment_data.get("status")
                id_transaccion_mp = payment_data.get("id")
                payer_email = payment_data.get("payer", {}).get("email", "cliente@vartens.com")

                if estado_pago == "approved" and subdominio_asociado:
                    # Actualizar Supabase a activo
                    supabase.table("proyectos").update({
                        "estado": "activo",
                        "fecha_activacion": "now()",
                        "id_pago_mp": str(id_transaccion_mp),
                        "estado_pago_mp": estado_pago
                    }).eq("subdominio", subdominio_asociado).execute()

                    print(f"✅ AUTOMATIZACIÓN MP: Proyecto '{subdominio_asociado}' activado.")
                    
                    # Ejecutar provisión y envío de credenciales automáticas
                    provisionar_servicio(subdominio_asociado, payer_email)

                elif estado_pago == "rejected" and subdominio_asociado:
                    supabase.table("proyectos").update({
                        "estado": "pago_rechazado",
                        "estado_pago_mp": estado_pago
                    }).eq("subdominio", subdominio_asociado).execute()
                    print(f"❌ AUTOMATIZACIÓN MP: Pago rechazado para '{subdominio_asociado}'.")

            # Responder siempre con 200 OK a Mercado Pago para confirmar recepción
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "received"}).encode('utf-8'))

        except Exception as e:
            print(f"❌ Error crítico en webhook MP: {str(e)}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
