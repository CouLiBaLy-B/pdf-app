"""
Tests pour le gestionnaire PDF
"""

import unittest
from core.pdf_manager import PDFManager


class TestPDFManager(unittest.TestCase):
    def setUp(self):
        """Configuration des tests"""
        self.pdf_manager = PDFManager()

    def tearDown(self):
        """Nettoyage après tests"""
        self.pdf_manager.close_current_pdf()

    def test_initialization(self):
        """Test de l'initialisation"""
        self.assertIsNone(self.pdf_manager.current_path)
        self.assertIsNone(self.pdf_manager.pdf_document)
        self.assertEqual(self.pdf_manager.current_page, 0)
        self.assertEqual(self.pdf_manager.total_pages, 0)

    def test_load_invalid_file(self):
        """Test de chargement d'un fichier invalide"""
        with self.assertRaises(Exception):
            self.pdf_manager.load_pdf("fichier_inexistant.pdf")


if __name__ == "__main__":
    unittest.main()
