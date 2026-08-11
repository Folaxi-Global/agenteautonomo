from core.db_client import get_supabase_client

def verificar_saldo_y_tesoreria():
    """Valida el estado financiero actual en la tabla de tesorería."""
    supabase = get_supabase_client()
    response = supabase.table("tesoreria").select("*").execute()
    
    if response.data:
        return response.data[0]
    
    # Si no existe registro de tesorería, se inicializa por defecto en 0
    nuevo_registro = {"saldo_operativo": 0.00}
    insert_res = supabase.table("tesoreria").insert(nuevo_registro).execute()
    return insert_res.data[0] if insert_res.data else nuevo_registro
