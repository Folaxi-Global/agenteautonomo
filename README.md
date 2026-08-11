# ⚡ A.U.R.A. (Autonomous Universal Revenue Agent)

Ecosistema de agentes autónomos basado en la nube, impulsado por **Google Gemini**, **Supabase** y desplegado en **Vercel** mediante Serverless Functions.

## 🚀 Arquitectura del Sistema
* **`api/`**: Contiene los endpoints serverless de backend (`aura.py`, `webhook.py`, `evaluar_ciclos.py`).
* **`core/`**: Lógica central de negocio, clientes de bases de datos y validaciones financieras de tesorería.
* **`templates/`**: Estructuras visuales de micro-SaaS ultra ligeros orientados a alta conversión.
* **`tests/`**: Pruebas unitarias para validación de flujos de IA y seguridad de saldo operativo.

## 🛠️ Configuración y Despliegue
1. Configura las variables de entorno en tu panel de Vercel basándote en `.env.example`.
2. Conecta las tablas de Supabase para tesorería y proyectos con el ciclo estricto de 14 días.
3. Programa los Cron Jobs automáticos (ej. mediante `cron-job.org`) apuntando a tus endpoints en `/api/aura`.
