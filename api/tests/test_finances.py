import unittest
from unittest.mock import patch, MagicMock

class TestFinancialGuard(unittest.TestCase):
    
    @patch("core.financial_guard.get_supabase_client")
    def test_verificacion_tesoreria_existente(self, mock_get_supabase):
        """Valida que la tesorería devuelva correctamente el saldo operativo actual."""
        # Simular respuesta de Supabase con datos de tesorería
        mock_supabase = MagicMock()
        mock_supabase.table().select().execute.return_value.data = [
            {"id": 1, "saldo_operativo": 150.50}
        ]
        mock_get_supabase.return_value = mock_supabase
        
        from core.financial_guard import verificar_saldo_y_tesoreria
        resultado = verificar_saldo_y_tesoreria()
        
        self.assertEqual(resultado["saldo_operativo"], 150.50)
        self.assertEqual(resultado["id"], 1)

    @patch("core.financial_guard.get_supabase_client")
    def t_test_tesoreria_vacia_inicializa(self, mock_get_supabase):
        """Valida que si la tabla está vacía, se inicialice por defecto en 0.0."""
        mock_supabase = MagicMock()
        # Primera llamada vacía, segunda llamada con el registro insertado
        mock_supabase.table().select().execute.return_value.data = []
        mock_supabase.table().insert().execute.return_value.data = [
            {"id": 99, "saldo_operativo": 0.00}
        ]
        mock_get_supabase.return_value = mock_supabase
        
        from core.financial_guard import verificar_saldo_y_tesoreria
        resultado = verificar_saldo_y_tesoreria()
        
        self.assertEqual(resultado["saldo_operativo"], 0.00)

if __name__ == "__main__":
    unittest.main()
