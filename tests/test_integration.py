"""
Tests d'intégration pour l'application complète
"""

import unittest
import tempfile
import os
from unittest.mock import patch
import tkinter as tk

from main_updated import PDFEditorApp


class TestIntegration(unittest.TestCase):
    def setUp(self):
        """Configuration des tests"""
        self.root = tk.Tk()
        self.root.withdraw()  # Cacher la fenêtre pendant les tests

    def tearDown(self):
        """Nettoyage après tests"""
        self.root.destroy()

    @patch("tkinter.filedialog.askopenfilename")
    def test_load_pdf_workflow(self, mock_filedialog):
        """Test du workflow complet de chargement PDF"""
        # Créer un fichier PDF temporaire pour les tests
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Simuler la sélection de fichier
            mock_filedialog.return_value = tmp_path

            # Créer l'application
            app = PDFEditorApp(self.root)

            # Tester le chargement (devrait échouer car le fichier n'est pas un vrai PDF)
            with patch("tkinter.messagebox.showerror") as mock_error:
                app.select_pdf()
                mock_error.assert_called_once()

        finally:
            # Nettoyer
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_app_initialization(self):
        """Test de l'initialisation de l'application"""
        app = PDFEditorApp(self.root)

        # Vérifier que les composants sont créés
        self.assertIsNotNone(app.pdf_manager)
        self.assertIsNotNone(app.config_manager)
        self.assertIsNotNone(app.notebook)
        self.assertEqual(len(app.tabs), 4)  # 4 onglets


if __name__ == "__main__":
    unittest.main()
