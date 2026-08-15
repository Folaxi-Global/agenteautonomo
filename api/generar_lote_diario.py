import os
import json
import random
import datetime
import requests
import time
import logging
from http.server import BaseHTTPRequestHandler
from google import genai
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

client = genai.Client(api_key=GEMINI_API_KEY)
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
    # Desactivado temporalmente para forzar el lote
    return False

def notificar_slack(proyecto_data):
    if not SLACK_WEBHOOK_URL: return
    payload = {
        "blocks": [
            {
                "type": "header", 
                "text": {"type": "plain_text", "text": f"🚀 SaaS Autónomo Desplegado: {proyecto_data['nombre_proyecto']}"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Detalle:* {proyecto_data['descripcion_oferta']}\n*Mercado:* {proyecto_data['pais_objetivo']}\n*Precio:* {proyecto_data['precio_mensual_local']} {proyecto_data['moneda']}\n*Subdominio:* {proyecto_data['subdominio_sugerido']}"}
            }
        ]
    }
    requests.post(SLACK_WEBHOOK_URL, json=payload)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            proyectos_creados = []
            
            # Generar los 5 micro-SaaS del ciclo autónomo
            for _ in range(5):
                mercado = random.choice(INFO_MERCADO)
                prompt = f"""Actúa como el CEO de Vartens. Genera un Micro-SaaS ultra ligero y comercializable para {mercado['pais']}.
                Debe ser un software automatizado de entrega digital inmediata.
                Responde ÚNICAMENTE con un objeto JSON (sin markdown adicional) con estas llaves exactas: 
                'nombre_proyecto', 'subdominio_sugerido', 'descripcion_oferta', 'precio_mensual_local', 'moneda'.
                """
                
                data = None
                for attempt in range(3):
                    try:
                        response = client.models.generate_content(
                            model=MODELO_AFORO,
                            contents=prompt,
                            config={"response_mime_type": "application/json"}
                        )
                        data = json.loads(response.text)
                        data.update({'iso_objetivo': mercado['iso'], 'pais_objetivo': mercado['pais']})
                        
                        if verificar_duplicidad(data["nombre_proyecto"]):
                            continue
                        break
                    except Exception:
                        if attempt == 2: data = None
                        time.sleep(1)
                
                if data:
                    subdominio = data["subdominio_sugerido"]
                    
                    # Estructura completa de inserción con pasarelas preparadas para cobro automático
                    nuevo_proyecto = {
                        "nombre_proyecto": data["nombre_proyecto"],
                        "subdominio": subdominio,
                        "descripcion_oferta": data["descripcion_oferta"],
                        "precio_mensual": data["precio_mensual_local"],
                        "moneda": data["moneda"],
                        "pais_objetivo": data["pais_objetivo"],
                        "iso_objetivo": data["iso_objetivo"],
                        "estado": "activo", # Listo para comercializar y prueba de 14 días
                        "fecha_creacion": datetime.datetime.now().isoformat(),
                        "stripe_link_anual": f"https://buy.stripe.com/autogenerado_{subdominio}",
                        "link_pago_mp": f"https://www.mercadopago.cl/checkout/v1/redirect?pref_id=auto_{subdominio}"
                    }
                    
                    supabase.table("proyectos").insert(nuevo_proyecto).execute()
                    notificar_slack(data)
                    proyectos_creados.append(data)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "total_generados": len(proyectos_creados), "data": proyectos_creados}).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
