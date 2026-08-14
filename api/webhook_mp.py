# api/webhook_mp.py
import os
import json
import mercadopago
from supabase import create_client, Client
from flask import request, jsonify
import hmac
import hashlib

# Configuración de seguridad (Firmas de MP)
# DEBES configurar este secreto en tu Dashboard de Vercel
MP_WEBHOOK_SECRET = os.environ.get("MP_WEBHOOK_SECRET") 

# Configuración de Base de Datos y MP
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
mp = mercadopago.SDK(MP_ACCESS_TOKEN)

def main(req, res):
    # Solo aceptamos POST
    if req.method != 'POST':
        return res.status(405).json({"status": "error", "message": "Método no permitido"})

    # --- SEGURIDAD: Validar firma de Mercado Pago (Crucial para evitar fraudes) ---
    # Obtenemos los headers y el cuerpo de la petición
    x_signature = req.headers.get('x-signature')
    x_request_id = req.headers.get('x-request-id')
    payload = req.get_data().decode('utf-8')

    if not x_signature or not x_request_id:
        print("❌ Webhook recibido sin firma de seguridad.")
        return res.status(403).json({"status": "error", "message": "Firma de seguridad faltante."})

    # Construimos la cadena para verificar la firma
    # Formato: ts:{timestamp};v1:{hash}
    ts_part = x_signature.split(';')[0]
    v1_part = x_signature.split(';')[1]
    
    # Obtenemos el timestamp puro (después de "ts:")
    timestamp = ts_part.split(':')[1]
    
    # Construimos el template del hash
    manifest = f"id:{req.get_json().get('data', {}).get('id')};request-id:{x_request_id};ts:{timestamp};"

    # Generamos nuestro hash localmente usando tu secreto
    calculated_hash = hmac.new(
        MP_WEBHOOK_SECRET.encode('utf-8'),
        manifest.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Comparamos nuestro hash con el que envía MP
    expected_hash = v1_part.split(':')[1]
    
    if not hmac.compare_digest(calculated_hash, expected_hash):
        print(f"❌ Firma de Webhook Inválida. Hash calculado: {calculated_hash}, Esperado: {expected_hash}")
        return res.status(403).json({"status": "error", "message": "Firma de seguridad inválida."})
    
    # --- FIN SEGURIDAD ---

    # Si la firma es correcta, procesamos el evento
    data = req.get_json()
    topic = data.get('topic', data.get('type')) # MP usa 'topic' o 'type' indistintamente

    print(f"✅ Webhook verificado. Evento recibido. Tipo: {topic}")

    if topic == 'payment' or topic == 'merchant_order':
        payment_id = data.get('data', {}).get('id')
        
        # Obtenemos los detalles del pago desde la API de MP
        payment_response = mp.payment().get(payment_id)
        payment_info = payment_response["response"]

        status = payment_info["status"] # Ej: 'approved', 'pending', 'rejected'
        external_reference = payment_info["external_reference"] # ESTE ES EL SUBDOMINIO!
        payer_email = payment_info["payer"]["email"]

        print(f"ℹ️ Detalles del pago: ID {payment_id}, Subdominio: {external_reference}, Estado: {status}")

        # --- AUTOMATIZACIÓN OPERATIVA ---
        if status == 'approved':
            print(f"🎉 PAGO APROBADO para el subdominio: {external_reference}")
            
            # 1. Actualizar la Base de Datos (Activar el servicio)
            update_data = {
                "estado": "activo",
                "pago_id": str(payment_id),
                "fecha_inicio_suscripcion": "now()" # O usa la fecha de MP
            }
            try:
                supabase.table("proyectos").update(update_data).eq("subdominio", external_reference).execute()
                print(f"✅ Base de datos actualizada para '{external_reference}'.")
                
                # 2. Provisionar el Acceso (Enviar email automático)
                # Aquí usarías la API de SendGrid o Resend para enviar credenciales
                # O activarías un script que despliega el acceso al subdominio.
                
                # Ejemplo conceptual de envío de email (usando una función auxiliar)
                # enviar_email_onboarding(payer_email, external_reference)
                
            except Exception as e:
                print(f"❌ Error al actualizar DB para '{external_reference}': {str(e)}")
                return res.status(500).json({"status": "error", "message": "Error interno del servidor"})

        elif status == 'rejected':
            print(f"⚠️ PAGO RECHAZADO para subdominio: {external_reference}. Email: {payer_email}")
            # Opcional: Actualizar DB a 'moroso' o enviar email de reintento
            try:
                supabase.table("proyectos").update({"estado": "moroso_inicial"}).eq("subdominio", external_reference).execute()
                # enviar_email_pago_fallido(payer_email, external_reference)
            except: pass

        elif status == 'cancelled':
            print(f"🛑 SUSCRIPCIÓN CANCELADA para subdominio: {external_reference}.")
            # Actualizar DB a 'cancelado'
            try:
                 supabase.table("proyectos").update({"estado": "cancelado"}).eq("subdominio", external_reference).execute()
            except: pass

    return jsonify({"status": "success"}), 200
