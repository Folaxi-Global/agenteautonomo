import os
import json
from http.server import BaseHTTPRequestHandler
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Consultar todos los proyectos activos o exitosos para listarlos en el directorio
            response = supabase.table("proyectos").select("*").in_("estado", ["activo", "exitoso"]).execute()
            proyectos = response.data if response.data else []

            # Construir la interfaz del Directorio Central (Hub de Tráfico)
            html_content = """
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>A.U.R.A. | Ecosistema de Micro-SaaS Autónomos</title>
                <style>
                    :root {
                        --bg-base: #0d1117;
                        --bg-card: #161b22;
                        --border-color: #30363d;
                        --text-main: #c9d1d9;
                        --text-muted: #8b949e;
                        --accent-blue: #58a6ff;
                        --accent-green: #3fb950;
                    }
                    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
                    body { background-color: var(--bg-base); color: var(--text-main); padding: 3rem 2rem; }
                    .container { max-width: 1000px; margin: 0 auto; }
                    header { text-align: center; margin-bottom: 3rem; }
                    h1 { color: #fff; font-size: 2.5rem; margin-bottom: 0.5rem; }
                    h1 span { color: var(--accent-blue); }
                    p.subtitle { color: var(--text-muted); font-size: 1.1rem; }
                    
                    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; }
                    .card { background: var(--bg-card); border: 1px solid var(--border-color); padding: 1.5rem; border-radius: 12px; transition: transform 0.2s, border-color 0.2s; display: flex; flex-direction: column; justify-content: space-between; }
                    .card:hover { transform: translateY(-4px); border-color: var(--accent-blue); }
                    .card h3 { color: #fff; font-size: 1.2rem; margin-bottom: 0.5rem; }
                    .card p { color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem; }
                    
                    .card-footer { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-color); pt: 1rem; margin-top: auto; padding-top: 1rem; }
                    .badge { font-size: 0.75rem; font-weight: bold; padding: 3px 8px; border-radius: 4px; text-transform: uppercase; }
                    .badge-activo { background: rgba(88, 166, 255, 0.15); color: var(--accent-blue); }
                    .badge-exitoso { background: rgba(63, 185, 80, 0.15); color: var(--accent-green); }
                    
                    .btn-visit { background: #238636; color: #fff; text-decoration: none; padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.85rem; font-weight: 600; transition: background 0.2s; }
                    .btn-visit:hover { background: #2ea043; }
                    
                    .empty-state { text-align: center; grid-column: 1 / -1; padding: 4rem; color: var(--text-muted); background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <header>
                        <h1>⚡ Ecosistema <span>A.U.R.A.</span></h1>
                        <p class="subtitle">Explora las herramientas digitales ultraligeras creadas y gestionadas de forma autónoma.</p>
                    </header>

                    <div class="grid">
            """

            if proyectos:
                for p in proyectos:
                    nombre = p.get('nombre_proyecto', 'Sin Nombre')
                    subdominio = p.get('subdominio', '#')
                    estado = p.get('estado', 'activo')
                    desc = p.get('descripcion_oferta', 'Herramienta de automatización inteligente.')
                    
                    html_content += f"""
                        <div class="card">
                            <div>
                                <h3>{nombre}</h3>
                                <p>{desc}</p>
                            </div>
                            <div class="card-footer">
                                <span class="badge badge-{estado}">{estado}</span>
                                <a href="https://{subdominio}.vercel.app" target="_blank" class="btn-visit">Abrir Herramienta</a>
                            </div>
                        </div>
                    """
            else:
                html_content += """
                        <div class="empty-state">
                            <h3>No hay micro-servicios públicos en este momento.</h3>
                            <p>El agente está analizando nuevos ciclos de ideación.</p>
                        </div>
                """

            html_content += """
                    </div>
                </div>
            </body>
            </html>
            """

            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "detalles": str(e)}).encode('utf-8'))
