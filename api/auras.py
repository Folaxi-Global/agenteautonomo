import os
import json
import random
import datetime
import requests
import time
import logging
from http.server import BaseHTTPRequestHandler
import google.generativeai as genai
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

genai.configure(api_key=GEMINI_API_KEY)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
MODELO_AFORO = "gemini-3.6-flash"

INFO_MERCADO = [
    {"pais": "México", "moneda": "MXN", "iso": "MX"},
    {"pais": "Colombia", "moneda": "COP", "iso": "CO"},
    {"pais": "Chile", "moneda": "CLP", "iso": "CL"},
    {"pais": "Argentina", "moneda": "ARS", "iso": "AR"},
    {"pais": "Perú", "moneda": "PEN", "iso": "PE"}
]

def verificar_duplicidad(nombre):
    """Evita registros duplicados en la base de datos."""
    res = supabase.table("proyectos").select("id").eq("nombre_proyecto", nombre).execute()
    return len(res.data) > 0

def notificar_slack(proyecto_data, saldo_actual):
    if not SLACK_WEBHOOK_URL: return
    
    payload = {
        "blocks": [
            {
                "type": "header", 
                "text": {"type": "plain_text", "text": f"🚀 Nuevo SaaS Desplegado: {proyecto_data['nombre_proyecto']}"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Detalle:* {proyecto_data['descripcion_oferta']}\n*Mercado:* {proyecto_data['pais_objetivo']}\n*Precio:* {proyecto_data['precio_mensual_local']} {proyecto_data['moneda']}\n*Subdominio:* {proyecto_data['subdominio_sugerido']}"}
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"💰 Saldo Operativo: ${saldo_actual:,.2f} USD | Estado: En Proceso de Build"}]
            }
        ]
    }
    requests.post(SLACK_WEBHOOK_URL, json=payload)

def aura_idear_y_registrar():
    mercado = random.choice(INFO_MERCADO)
    
    # Prompt optimizado para un SaaS que se pueda automatizar (Landing + Entrega)
    prompt = f"""Actúa como el CEO de Vartens. Genera un Micro-SaaS ultra ligero para {mercado['pais']}.
    Debe ser un producto de software que pueda entregarse automáticamente (acceso a web/dashboard).
    Responde ÚNICAMENTE en JSON con estas llaves exactas: 
    'nombre_proyecto', 'subdominio_sugerido', 'descripcion_oferta', 'precio_mensual_local', 'moneda'.
    """
    
    # Generación con reintentos
    for attempt in range(3):
        try:
            model = genai.GenerativeModel(MODELO_AFORO)
            response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            data = json.loads(response.text)
            data.update({'iso_objetivo': mercado['iso'], 'pais_objetivo': mercado['pais']})
            
            # Validación de duplicidad
            if verificar_duplicidad(data["nombre_proyecto"]):
                logger.warning(f"Proyecto {data['nombre_proyecto']} ya existe. Reintentando...")
                continue
            break
        except Exception as e:
            if attempt == 2: raise Exception(f"IA_Fallo: {str(e)}")
            time.sleep(2)

    # Inserción en Supabase con estado inicial 'desplegando'
    nuevo_proyecto = {
        "nombre_proyecto": data["nombre_proyecto"],
        "subdominio": data["subdominio_sugerido"],
        "descripcion_oferta": data["descripcion_oferta"],
        "precio_mensual": data["precio_mensual_local"],
        "moneda": data["moneda"],
        "pais_objetivo": data["pais_objetivo"],
        "estado": "desplegando",
        "fecha_creacion": datetime.datetime.now().isoformat()
    }
    
    supabase.table("proyectos").insert(nuevo_proyecto).execute()
    
    # Notificación y retorno
    notificar_slack(data, 0.0) 
    return data

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            resultado = aura_idear_y_registrar()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "data": resultado}).encode())
        except Exception as e:
            logger.error(f"Error en ciclo autónomo: {str(e)}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
