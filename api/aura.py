import os
import json
import random
import datetime
import requests
from http.server import BaseHTTPRequestHandler
import google.generativeai as genai
from supabase import create_client, Client

# --- CONFIGURACIÓN CORPORATIVA Y SEGURIDAD ---
# (Todas estas deben estar configuradas en el Dashboard de Vercel)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
# Webhook para tu Dashboard en Slack (Canal #operaciones)
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

# Inicialización de Clientes
genai.configure(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- CONFIGURACIÓN DEL MOTOR DE IA (ULTRA PRO) ---
# Intentamos usar el modelo más avanzado disponible
MODELO_AFORO = "gemini-3.6-flash" 

try:
    model = genai.GenerativeModel(MODELO_AFORO)
    print(f"✅ AURA Smart Core initialized. Model: {MODELO_AFORO}")
except Exception as e:
    print(f"⚠️ Experimental model {MODELO_AFORO} init failed: {str(e)}")
    print("⬇️ Falling back to: gemini-1.5-flash")
    model = genai.GenerativeModel('gemini-1.5-flash')
    MODELO_AFORO = "gemini-1.5-flash (fallback)"

# --- DATOS DE LOCALIZACIÓN LATAM ---
# Diversificamos el mercado objetivo automáticamente
INFO_MERCADO = [
    {"pais": "México", "moneda": "MXN", "iso": "MX"},
    {"pais": "Colombia", "moneda": "COP", "iso": "CO"},
    {"pais": "Chile", "moneda": "CLP", "iso": "CL"},
    {"pais": "Argentina", "moneda": "ARS", "iso": "AR"},
    {"pais": "Perú", "moneda": "PEN", "iso": "PE"}
]

# --- FUNCIONES AUXILIARES DE GESTIÓN ---

def verificar_tesoreria():
    """Obtiene el saldo operativo actual desde Supabase."""
    try:
        response = supabase.table("tesoreria").select("saldo_operativo").eq("id", 1).execute()
        return response.data[0]["saldo_operativo"] if response.data else 0.0
    except Exception as e:
        print(f"❌ Error checking treasury: {str(e)}")
        return 0.0

def notificar_slack(proyecto_data, saldo_actual):
    """Envía un reporte detallado al Dashboard de Slack vía Webhook."""
    if not SLACK_WEBHOOK_URL:
        print("⚠️ Slack Webhook URL not found. Skipping notification.")
        return

    sub_sugerido = proyecto_data.get('subdominio_sugerido')
    pais = proyecto_data.get('pais_objetivo')
    precio = proyecto_data.get('precio_mensual_local')
    moneda = proyecto_data.get('moneda')

    # Construcción del mensaje enriquecido (Block Kit)
    slack_payload = {
        "text": f"🚀 Nuevo Micro-SaaS Desplegado: {proyecto_data['nombre_proyecto']}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🤖 A.U.R.A. ha lanzado un nuevo activo digital",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Nombre:* \n{proyecto_data['nombre_proyecto']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*ID de Proyecto:* \n{sub_sugerido}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Mercado Objetivo:* \n{pais} ({iso})"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Modelo IA:* \n{MODELO_AFORO}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Precio Suscripción:* \n{precio} {moneda} / mes"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Estado del Servicio:* \n🟢 Desplegado y Esperando Pago"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Descripción de la Oferta:* \n{proyecto_data['descripcion_oferta']}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"💰 Saldo Operativo Actual: ${saldo_actual:,.2f} USD | Factoría activa (Lote 5/5)"
                    }
                ]
            }
        ]
    }

    try:
        requests.post(SLACK_WEBHOOK_URL, json=slack_payload)
        print("✅ Slack notification sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send Slack notification: {str(e)}")

# --- CEREBRO AUTÓNOMO (EL NÚCLEO DEL AGENTE) ---

def aura_idear_y_registrar():
    """
    1. Selecciona mercado LatAm.
    2. Llama a Gemini 3.6-Flash para idear el SaaS.
    3. Registra en Supabase.
    4. Notifica a Slack.
    """
    
    # 1. Localización Automática
    mercado_actual = random.choice(INFO_MERCADO)
    pais_obj = mercado_actual["pais"]
    moneda_obj = mercado_actual["moneda"]
    iso_obj = mercado_actual["iso"]

    print(f"🌍 AURA initiating ideation for market: {pais_obj} ({moneda_obj})...")

    # 2. Prompt de Ingeniería Inversa (Ultra Pro - Español LatAm)
    # Instruimos a la IA para pensar como un Growth Hacker de PYMEs en LatAm
    prompt = (
        f"Eres A.U.R.A., CEO autónomo de un holding de micro-SaaS hiper-exitoso. "
        f"Tu objetivo es idear un micro-servicio web ultra ligero, totalmente automatizable (sin intervención humana) "
        f"para el mercado de {pais_obj}. "
        f"El producto debe resolver un dolor agudo de las PYMEs locales en dicho país. "
        f"El concepto debe estar redactado en español neutro, persuasivo y adaptado al contexto cultural de {pais_obj}. "
        f"Define un nombre de marca atractivo y un subdominio único (ej: 'facturarapido-mx'). "
        f"Establece un precio de suscripción mensual competitivo en {moneda_obj} (ej: 299 {moneda_obj}). "
        f"Devuélvelo ESTRICTAMENTE como un objeto JSON sin formato markdown, con las claves: "
        f"'nombre_proyecto', 'subdominio_sugerido', 'descripcion_oferta', 'precio_mensual_local', 'moneda', 'iso_pais'."
    )

    configuracion_pro = genai.types.GenerationConfig(
        response_mime_type="application/json",
        temperature=0.7, # Creatividad equilibrada para negocios
        top_k=40,
        top_p=0.95
    )

    try:
        response = model.generate_content(prompt, generation_config=configuracion_pro)
        idea_data = json.loads(response.text)
    except Exception as e:
        print(f"❌ Gemini API Generation Error: {str(e)}")
        raise Exception("IA_Generation_Failed")

    # Validar estructura del JSON recibido
    required_keys = ['nombre_proyecto', 'subdominio_sugerido', 'descripcion_oferta', 'precio_mensual_local', 'moneda']
    if not all(key in idea_data for key in required_keys):
        print(f"❌ Invalid JSON structure received from IA: {idea_data}")
        raise Exception("Invalid_IA_Response")

    # Agregar el ISO al objeto de idea para uso en Slack
    idea_data['iso_objetivo'] = iso_obj
    idea_data['pais_objetivo'] = pais_obj

    # 3. Registro transaccional en Supabase (Single Source of Truth)
    print(f"💾 Registering new project: {idea_data['nombre_proyecto']} in Supabase...")
    
    # Datos completos para la base de datos maestra
    timestamp_despliegue = datetime.datetime.now().isoformat()
    
    nuevo_proyecto = {
        "nombre_proyecto": idea_data["nombre_proyecto"],
        "subdominio": idea_data["subdominio_sugerido"],
        "descripcion_oferta": idea_data["descripcion_oferta"],
        "precio_mensual": idea_data["precio_mensual_local"],
        "moneda": idea_data["moneda"],
        "pais_objetivo": pais_obj,
        "iso_pais": iso_obj,
        "estado": "desplegando", # El ciclo de vida apenas comienza
        "fecha_creacion": timestamp_despliegue,
        "modelo_ia": MODELO_AFORO, # Trazabilidad
        "stripe_link_anual": "pendiente", # Se generará luego
        "link_pago_mp": "pendiente" # Se generará en el siguiente script
    }
    
    try:
        supabase.table("proyectos").insert(nuevo_proyecto).execute()
        print(f"✅ Project '{idea_data['subdominio_sugerido']}' registered in DB.")
    except Exception as e:
        print(f"❌ Supabase Insert Error: {str(e)}")
        raise Exception("DB_Registration_Failed")

    # 4. Notificación Dashboard Slack
    saldo = verificar_tesoreria()
    notificar_slack(idea_data, saldo)

    return idea_data

# --- MANEJADOR DE LA SERVERLESS FUNCTION ---

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """
        Endpoint principal activado por CRON Job (Vercel).
        Ruta: /api/auras
        """
        # Autenticación básica de seguridad (opcional pero recomendada para CRON)
        # auth_header = self.headers.get('Authorization')
        # if auth_header != f"Bearer {os.environ.get('CRON_SECRET')}":
        #     self.send_response(401)
        #     self.end_headers()
        #     return

        try:
            # Ejecución del Ciclo de Vida Autónomo
            print("⏱️ [CRON] Executing AURA Lifecycle Batch...")
            resultado_idea = aura_idear_y_registrar()
            
            # Respuesta HTTP de éxito
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            respuesta_json = {
                "status": "success",
                "timestamp": datetime.datetime.now().isoformat(),
                "batch_process": "ideacion_y_registro",
                "modelo_ia": MODELO_AFORO,
                "proyecto_iniciado": {
                    "nombre": resultado_idea["nombre_proyecto"],
                    "subdominio": resultado_idea["subdominio_sugerido"],
                    "pais": resultado_idea["pais_objetivo"]
                }
            }
            self.wfile.write(json.dumps(respuesta_json, ensure_ascii=False).encode('utf-8'))
            print("✅ [CRON] Batch Cycle Completed Successfully.")
            
        except Exception as e:
            # Manejo de errores global
            error_type = str(e)
            print(f"❌ [CRON] CRITICAL ERROR in AURA Lifecycle: {error_type}")
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            error_response = {
                "status": "error",
                "timestamp": datetime.datetime.now().isoformat(),
                "message": "Critical error during autonomous lifecycle.",
                "error_code": error_type
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))

# NOTA: BaseHTTPRequestHandler no requiere if __name__ == '__main__':
# Vercel invoca la clase handler directamente al recibir la petición en /api/auras
