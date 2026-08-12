import os
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from google import genai
from google.genai import types
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # 1. Analizar si se solicitó un proyecto específico por parámetro (ej: /api/marketing_viral?subdominio=quickog)
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)
            subdominio_solicitado = query_params.get("subdominio", [None])[0]

            if subdominio_solicitado:
                response = supabase.table("proyectos").select("*").eq("subdominio", subdominio_solicitado).execute()
            else:
                # Si no hay parámetro, toma el proyecto activo más reciente del ecosistema
                response = supabase.table("proyectos").select("*").eq("estado", "activo").order("created_at", desc=True).limit(1).execute()
            
            if not response.data:
                self.send_response(404)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                error_res = {"status": "error", "mensaje": "No se encontró ningún proyecto activo para generar marketing."}
                self.wfile.write(json.dumps(error_res, ensure_ascii=False).encode('utf-8'))
                return

            proyecto = response.data[0]
            nombre = proyecto.get("nombre_proyecto")
            subdominio = proyecto.get("subdominio")
            descripcion = proyecto.get("descripcion_oferta", "Herramienta digital inteligente optimizada para la conversión.")

            # 2. Prompt Pro de Growth Hacking y Psicología de Consumo con Gemini
            prompt = (
                f"Eres el Director de Marketing y Crecimiento de un holding global de micro-SaaS. "
                f"Diseña una estrategia de marketing viral de alto rendimiento para el siguiente producto:\n"
                f"- Nombre del Micro-SaaS: {nombre}\n"
                f"- URL de Acceso: {subdominio}.vercel.app\n"
                f"- Propuesta de Valor: {descripcion}\n\n"
                f"Tu objetivo es conseguir tracción masiva en redes sociales (TikTok, Reels, LinkedIn). "
                f"Responde estrictamente en formato JSON válido con esta estructura exacta:\n"
                f"{\n"
                f"  \"gancho_video_3s\": \"Frase visual y auditiva para los primeros 3 segundos del video que rompa el patrón de scroll.\",\n"
                f"  \"guion_cuerpo\": \"Explicación rápida del problema y cómo este micro-SaaS lo soluciona en menos de 20 segundos.\",\n"
                f"  \"call_to_action\": \"Llamada a la acción persuasiva para ir al link del perfil o bio.\",\n"
                f"  \"copy_publicacion\": \"El texto completo optimizado para la descripción del post con llamadas a la acción claras.\",\n"
                f"  \"hashtags_virales\": [\"#hashtag1\", \"#hashtag2\", \"#hashtag3\"],\n"
                f"  \"estrategia_growth_hacking\": \"Una acción de guerrilla digital exacta para conseguir los primeros clientes hoy mismo.\"\n"
                f"}"
            )

            # 3. Llamada al motor inteligente usando Gemini Flash
            ai_response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )

            estrategia_marketing = json.loads(ai_response.text)

            # 4. Respuesta HTTP limpia y optimizada con CORS
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            resultado = {
                "status": "success",
                "agente": "A.U.R.A. Marketing Engine",
                "proyecto_objetivo": nombre,
                "url_publica": f"https://{subdominio}.vercel.app",
                "campaña": estrategia_marketing
            }
            self.wfile.write(json.dumps(resultado, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            error_res = {"status": "error", "detalles": str(e)}
            self.wfile.write(json.dumps(error_res, ensure_ascii=False).encode('utf-8'))
