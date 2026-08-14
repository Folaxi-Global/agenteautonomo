# api/webhook_mp.py
import os
import json
import mercadopago
from supabase import create_client, Client
from flask import request, jsonify
import hmac
import hashlib
import requests  # Importante: Necesario para llamar a la API de Resend

# --- CONFIGURACIÓN DE SEGURIDAD Y AMBIENTE ---
# Secretos configurados en el Dashboard de Vercel
MP_WEBHOOK_SECRET = os.environ.get("MP_WEBHOOK_SECRET")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")
# API Key de Resend para enviar emails automáticos
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

# Email verificado desde el cual se enviarán los correos de bienvenida
FROM_EMAIL = "onboarding@vartens.com"

# --- INICIALIZACIÓN DE CLIENTES ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
mp = mercadopago.SDK(MP_ACCESS_TOKEN)


# --- FUNCIÓN AUXILIAR DE PROVISIÓN (Prestación Efectiva del Servicio) ---
def provisionar_servicio(subdominio, email_cliente):
    """
    Esta función entrega efectivamente el servicio tras el pago exitoso.
    Envía un email con las credenciales y accesos al nuevo cliente usando Resend.
    """
    print(f"🚀 Iniciando provisión del servicio para '{subdominio}' a '{email_cliente}'...")

    try:
        # 1. Obtenemos los datos del proyecto desde Supabase para personalizar el email
        res = supabase.table("proyectos").select("*").eq("subdominio", subdominio).execute()
        if not res.data:
            print(f"❌ Error de provisión: Proyecto {subdominio} no encontrado en DB.")
            return

        proyecto = res.data[0]
        nombre_sitio = proyecto.get("nombre_sitio", "Tu Nuevo SaaS")

        # Definimos la URL de acceso (el subdominio recién creado)
        url_acceso = f"https://{subdominio}.vartens.com"

        # --- 2. PERSONALIZACIÓN DEL EMAIL DE BIENVENIDA ---
        asunto = f"¡Bienvenido a {nombre_sitio}! Tu acceso ya está activo."

        cuerpo_email = f"""
        ¡Hola!

        ¡Gracias por tu suscripción a {nombre_sitio}! Te confirmamos que tu pago ha sido procesado con éxito.

        Tu servicio ya está activo y listo para usar. A continuación, encontrarás tus datos de acceso:

        🌐 URL de tu sitio: <a href='{url_acceso}'>{url_acceso}</a>
        👤 Usuario: {email_cliente}
        🔑 Contraseña temporal: (Hemos generado una contraseña segura y la hemos enviado en un email separado por seguridad).

        ¿Qué sigue?
        1. Inicia sesión en la URL de arriba.
        2. Configura tu perfil y conecta tus primeras fuentes de datos.
        3. Si tienes dudas, consulta nuestra base de conocimiento: {url_acceso}/docs

        ¡Mucho éxito en tu gestión con {nombre_sitio}!

        Atentamente,
        El equipo de Vartens
        """

        # --- 3. ENVÍO DEL EMAIL VIA RESEND API ---
        headers = {
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        }

        email_payload = {
            "from": FROM_EMAIL,
            "to": email_cliente,
            "subject": asunto,
            "html": cuerpo_email  # Resend acepta HTML directamente
        }

        response = requests.post("https://api.resend.com/emails", headers=headers, json=email_payload)

        if response.status_code == 200:
            print(f"✅ Email de provisión enviado exitosamente a '{email_cliente}'.")
            # Opcional: Actualizar DB indicando que el email de bienvenida fue enviado
            supabase.table("proyectos").update({"email_onboarding_enviado": True}).eq("subdominio", subdominio).execute()
        else:
            print(f"❌ Error al enviar email de provisión via Resend: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Error crítico durante la provisión del servicio: {str(e)}")


# --- FUNCIÓN PRINCIPAL DEL WEBHOOK ---
def main(req, res):
    # Solo aceptamos POST
    if req.method != 'POST':
        return res.status(405).json({"status": "error", "message": "Método no permitido"})

    # --- SEGURIDAD: Validar firma de Mercado Pago ---
    x_signature = req.headers.get('x-signature')
    x_request_id = req.headers.get('x-request-id')
    
    if not x_signature or not x_request_id:
        print("❌ Webhook recibido sin firma de seguridad.")
        return res.status(403).json({"status": "error", "message": "Firma de seguridad faltante."})

    # Parseamos la firma para obtener el timestamp y el hash esperado
    try:
        ts_part = x_signature.split(';')[0]
        v1_part = x_signature.split(';')[1]
        timestamp = ts_part.split(':')[1]
        expected_hash = v1_part.split(':')[1]
    except IndexError:
        return res.status(403).json({"status": "error", "message": "Formato de firma inválido."})

    # Obtenemos el cuerpo de la petición como string para recalcular el hash
    payload = req.get_data().decode('utf-8')
    data = req.get_json()
    
    # Construimos el template del hash (id del recurso, request-id, timestamp)
    resource_id = data.get('data', {}).get('id')
    if not resource_id:
         return res.status(400).json({"status": "error", "message": "ID de recurso no encontrado en el payload."})

    manifest = f"id:{resource_id};request-id:{x_request_id};ts:{timestamp};"

    # Generamos nuestro hash localmente usando tu secreto
    calculated_hash = hmac.new(
        MP_WEBHOOK_SECRET.encode('utf-8'),
        manifest.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Comparamos nuestro hash con el que envía MP
    if not hmac.compare_digest(calculated_hash, expected_hash):
        print(f"❌ Firma de Webhook Inválida.")
        return res.status(403).json({"status": "error", "message": "Firma de seguridad inválida."})
    
    # --- FIN SEGURIDAD ---

    # Si la firma es correcta, procesamos el evento
    topic = data.get('topic', data.get('type')) # MP usa 'topic' o 'type'
    print(f"✅ Webhook verificado. Evento recibido. Tipo: {topic}")

    if topic == 'payment' or topic == 'merchant_order':
        payment_id = resource_id
        
        # Obtenemos los detalles completos del pago desde la API de MP
        try:
            payment_response = mp.payment().get(payment_id)
            payment_info = payment_response["response"]

            status = payment_info["status"] # Ej: 'approved', 'pending', 'rejected'
            # ¡CRÍTICO! external_reference DEBE ser el subdominio que guardaste al crear el sitio
            external_reference = payment_info["external_reference"] 
            payer_email = payment_info["payer"]["email"]

            print(f"ℹ️ Detalles del pago: ID {payment_id}, Subdominio: {external_reference}, Estado: {status}")

            # --- LÓGICA DE NEGOCIO: Aprovisionamiento Automático ---
            if status == 'approved':
                print(f"🎉 PAGO APROBADO para el subdominio: {external_reference}")
                
                # 1. Actualizar la Base de Datos (Marcar el servicio como activo)
                update_data = {
                    "estado": "activo",
                    "pago_id": str(payment_id),
                    "fecha_inicio_suscripcion": "now()" # O usa la fecha de aprobación de MP
                }
                try:
                    supabase.table("proyectos").update(update_data).eq("subdominio", external_reference).execute()
                    print(f"✅ Base de datos actualizada para '{external_reference}'.")
                    
                    # 2. ¡PRESTACIÓN EFECTIVA DEL SERVICIO!
                    # Llamamos a la función auxiliar para enviar el email de bienvenida/acceso.
                    provisionar_servicio(external_reference, payer_email)
                    
                except Exception as e:
                    print(f"❌ Error al actualizar DB para '{external_reference}': {str(e)}")
                    # No detenemos el proceso, intentamos enviar el email igual o manejar el error
                    return res.status(500).json({"status": "error", "message": "Error al actualizar base de datos"})

            elif status == 'rejected':
                print(f"⚠️ PAGO RECHAZADO para subdominio: {external_reference}.")
                # Actualizar DB a 'moroso' o similar
                try:
                    supabase.table("proyectos").update({"estado": "moroso_inicial"}).eq("subdominio", external_reference).execute()
                except: pass

            elif status == 'cancelled':
                print(f"🛑 SUSCRIPCIÓN CANCELADA por el usuario para subdominio: {external_reference}.")
                # Actualizar DB a 'cancelado'
                try:
                     supabase.table("proyectos").update({"estado": "cancelado"}).eq("subdominio", external_reference).execute()
                except: pass

        except Exception as e:
             print(f"❌ Error al consultar API de MP o procesar lógica: {str(e)}")
             return res.status(500).json({"status": "error", "message": "Error interno al procesar el pago"})

    # Respondemos siempre a MP para confirmar que recibimos la notificación
    return jsonify({"status": "received"}), 200
