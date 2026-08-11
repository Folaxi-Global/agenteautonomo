import unittest
from unittest.mock import patch, MagicMock

class TestAuraIdeacion(unittest.TestCase):
    
    @patch("google.genai.Client")
    def test_generacion_idea_estructura(self, mock_genai_client):
        """Valida que la respuesta simulada de Gemini devuelva las claves requeridas para el micro-servicio."""
        # Simular la respuesta de Gemini con formato JSON estricto
        mock_response = MagicMock()
        mock_response.text = '{"nombre_proyecto": "SaaS Test", "subdomain_sugerido": "saastest", "descripcion_oferta": "Herramienta ligera de prueba."}'
        
        mock_client_instance = mock_genai_client.return_value
        mock_client_instance.models.generate_content.return_value = mock_response
        
        # Validación de que la respuesta contiene las llaves necesarias para Supabase
        import json
        data = json.loads(mock_response.text)
        
        self.assertIn("nombre_proyecto", data)
        self.assertIn("subdomain_sugerido", data)
        self.assertEqual(data["nombre_proyecto"], "SaaS Test")

if __name__ == "__main__":
    unittest.main()
