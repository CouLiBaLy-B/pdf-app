"""
Tests pour le service de texte
"""

import unittest
from unittest.mock import Mock
from services.text_service import TextService


class TestTextService(unittest.TestCase):
    def setUp(self):
        """Configuration des tests"""
        self.mock_pdf_manager = Mock()
        self.text_service = TextService(self.mock_pdf_manager)

    def test_add_text_no_pdf(self):
        """Test d'ajout de texte sans PDF chargé"""
        self.mock_pdf_manager.pdf_document = None

        with self.assertRaises(Exception) as context:
            self.text_service.add_text("Test", 100, 100, 12, "black")

        self.assertIn("Aucun PDF chargé", str(context.exception))

    def test_extract_text_no_pdf(self):
        """Test d'extraction de texte sans PDF chargé"""
        self.mock_pdf_manager.pdf_document = None

        with self.assertRaises(Exception) as context:
            self.text_service.extract_page_text(0)

        self.assertIn("Aucun PDF chargé", str(context.exception))


if __name__ == "__main__":
    unittest.main()
