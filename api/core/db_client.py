import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Inicializa y retorna el cliente centralizado de Supabase usando variables de entorno."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Las credenciales de Supabase (SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY) no están configuradas.")
        
    return create_client(supabase_url, supabase_key)
