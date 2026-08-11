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
            # 1. Obtener datos de tesorería
            tesoreria_res = supabase.table("tesoreria").select("*").execute()
            saldo_operativo = 0.00
            if tesoreria_res.data:
                saldo_operativo = float(tesoreria_res.data[0].get('saldo_operativo', 0.00))

            # 2. Obtener lista de proyectos
            proyectos_res = supabase.table("proyectos").select("*").execute()
            proyectos = proyectos_res.data if proyectos_res.data else []

            # Calcular métricas
            total_proyectos = len(proyectos)
            activos = sum(1 for p in proyectos if p.get('estado') == 'activo')
            exitosos = sum(1 for p in proyectos if p.get('estado') == 'exitoso')

            # 3. Construir la interfaz Pro HTML/CSS/JS
            html_content = f"""
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>A.U.R.A. | Pro Command Center</title>
                <style>
                    :root {{
                        --bg-base: #0d1117;
                        --bg-card: #161b22;
                        --border-color: #30363d;
                        --text-main: #c9d1d9;
                        --text-muted: #8b949e;
                        --accent-blue: #58a6ff;
                        --accent-green: #3fb950;
                        --accent-yellow: #d29922;
                    }}
                    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
                    body {{ background-color: var(--bg-base); color: var(--text-main); padding: 2.5rem; }}
                    
                    header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 1.5rem; margin-bottom: 2rem; }}
                    .title-area h1 {{ color: var(--accent-blue); font-size: 1.8rem; display: flex; align-items: center; gap: 0.5rem; }}
                    .title-area p {{ color: var(--text-muted); font-size: 0.9rem; margin-top: 0.3rem; }}
                    
                    .status-badge {{ background: rgba(35, 134, 54, 0.15); color: var(--accent-green); border: 1px solid rgba(63, 185, 80, 0.4); padding: 6px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600; display: flex; align-items: center; gap: 6px; }}
                    .pulse {{ width: 8px; height: 8px; background: var(--accent-green); border-radius: 50%; box-shadow: 0 0 8px var(--accent-green); animation: pulse 2s infinite; }}
                    @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} 100% {{ opacity: 1; }} }}

                    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.5rem; margin-bottom: 2.5rem; }}
                    .card {{ background: var(--bg-card); border: 1px solid var(--border-color); padding: 1.5rem; border-radius: 12px; position: relative; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.2); transition: transform 0.2s, border-color 0.2s; }}
                    .card:hover {{ transform: translateY(-3px); border-color: var(--accent-blue); }}
                    .card h3 {{ color: var(--text-muted); font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.5rem; }}
                    .card .value {{ font-size: 2.2rem; font-weight: bold; color: #fff; }}
                    .card .value.green {{ color: var(--accent-green); }}

                    .table-container {{ background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }}
                    .table-header {{ padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; }}
                    .table-header h2 {{ font-size: 1.1rem; color: #fff; }}
                    
                    table {{ width: 100%; border-collapse: collapse; text-align: left; }}
                    th, td {{ padding: 1rem 1.5rem; border-bottom: 1px solid var(--border-color); font-size: 0.95rem; }}
                    th {{ background: #1f242d; color: var(--accent-blue); font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.5px; }}
                    tr:last-child td {{ border-bottom: none; }}
                    tr:hover td {{ background: rgba(255,255,255,0.01); }}
                    
                    .tag {{ padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; }}
                    .tag-activo {{ background: rgba(210, 153, 34, 0.15); color: var(--accent-yellow); border: 1px solid rgba(210, 153, 34, 0.3); }}
                    .tag-exitoso {{ background: rgba(63, 185, 80, 0.15); color: var(--accent-green); border: 1px solid rgba(63, 185, 80, 0.3); }}
                    
                    .empty-state {{ text-align: center; padding: 3rem; color: var(--text-muted); }}
                </style>
                <script>
                    // Auto-refrescar el dashboard cada 30 segundos para mantener datos en vivo
                    setTimeout(() => {{ window.location.reload(); }}, 30000);
                </script>
            </head>
            <body>
                <header>
                    <div class="title-area">
                        <h1>⚡ A.U.R.A. Pro Command Center</h1>
                        <p>Supervisión autónoma en tiempo real de infraestructura y tesorería.</p>
                    </div>
                    <div class="status-badge">
                        <span class="pulse"></span> Nodo Activo (Edge)
                    </div>
                </header>

                <div class="grid">
                    <div class="card">
                        <h3>Saldo Operativo</h3>
                        <div class="value green">${saldo_operativo:,.2f}</div>
                    </div>
                    <div class="card">
                        <h3>Total Proyectos</h3>
                        <div class="value">{total_proyectos}</div>
                    </div>
                    <div class="card">
                        <h3>En Prueba (14 Días)</h3>
                        <div class="value">{activos}</div>
                    </div>
                    <div class="card">
                        <h3>Monetizados / Exitosos</h3>
                        <div class="value green">{exitosos}</div>
                    </div>
                </div>

                <div class="table-container">
                    <div class="table-header">
                        <h2>Micro-Servicios Desplegados</h2>
                        <span style="font-size: 0.85rem; color: var(--text-muted);">Actualización automática cada 30s</span>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>Nombre del Proyecto</th>
                                <th>Subdominio Registrado</th>
                                <th>Estado del Ciclo</th>
                            </tr>
                        </thead>
                        <tbody>
            """

            if proyectos:
                for p in proyectos:
                    estado = p.get('estado', 'activo')
                    tag_class = f"tag tag-{estado}"
                    html_content += f"""
                            <tr>
                                <td style="font-weight: 600; color: #fff;">{p.get('nombre_proyecto', 'Sin Nombre')}</td>
                                <td style="color: var(--accent-blue);">{p.get('subdominio', 'N/A')}</td>
                                <td><span class="{tag_class}">{estado}</span></td>
                            </tr>
                    """
            else:
                html_content += """
                            <tr>
                                <td colspan="3" class="empty-state">No hay micro-servicios registrados todavía. Esperando ciclo de ideación del agente.</td>
                            </tr>
                """

            html_content += """
                        </tbody>
                    </table>
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
            error_json = {"status": "error", "detalles": str(e)}
            self.wfile.write(json.dumps(error_json).encode('utf-8'))
