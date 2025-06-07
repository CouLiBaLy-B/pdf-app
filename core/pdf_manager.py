"""
Gestionnaire principal pour les opérations PDF
"""

import fitz
import PyPDF2
import tempfile
import os
from datetime import datetime


class PDFManager:
    def __init__(self):
        self.pdf_document = None
        self.pdf_reader = None
        self.current_path = None
        self.total_pages = 0
        self.current_page = 0

    def load_pdf(self, file_path):
        """Charge un fichier PDF"""
        try:
            # Fermer le document précédent
            self.close_current_pdf()

            # Charger avec PyMuPDF pour l'édition
            self.pdf_document = fitz.open(file_path)

            # Charger avec PyPDF2 pour les métadonnées
            with open(file_path, "rb") as file:
                self.pdf_reader = PyPDF2.PdfReader(file)

            self.current_path = file_path
            self.total_pages = len(self.pdf_document)
            self.current_page = 0

            return True

        except Exception as e:
            raise Exception(f"Impossible de charger le PDF: {str(e)}")

    def get_page(self, page_num=None):
        """Retourne une page spécifique"""
        if not self.pdf_document:
            return None

        if page_num is None:
            page_num = self.current_page

        if 0 <= page_num < self.total_pages:
            return self.pdf_document[page_num]
        return None

    def get_metadata(self):
        """Retourne les métadonnées du PDF"""
        if not self.pdf_reader or not self.pdf_reader.metadata:
            return {}

        metadata = {}
        raw_metadata = self.pdf_reader.metadata

        metadata["title"] = raw_metadata.get("/Title", "") or ""
        metadata["author"] = raw_metadata.get("/Author", "") or ""
        metadata["subject"] = raw_metadata.get("/Subject", "") or ""
        metadata["creator"] = raw_metadata.get("/Creator", "") or ""
        metadata["producer"] = raw_metadata.get("/Producer", "") or ""
        metadata["keywords"] = raw_metadata.get("/Keywords", "") or ""
        metadata["creation_date"] = str(raw_metadata.get("/CreationDate", ""))
        metadata["modification_date"] = str(raw_metadata.get("/ModDate", ""))

        return metadata

    def save_with_metadata(self, output_path, metadata_dict):
        """Sauvegarde le PDF avec les métadonnées mises à jour"""
        if not self.pdf_document:
            raise Exception("Aucun PDF chargé")

        # Sauvegarder les modifications de contenu
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_file.close()

        self.pdf_document.save(temp_file.name)

        # Traiter les métadonnées avec PyPDF2
        with open(temp_file.name, "rb") as input_file:
            pdf_reader = PyPDF2.PdfReader(input_file)
            pdf_writer = PyPDF2.PdfWriter()

            # Copier toutes les pages
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)

            # Préparer les métadonnées
            metadata = {}
            for key, value in metadata_dict.items():
                if value:
                    pdf_key = f"/{key.title()}"
                    metadata[pdf_key] = value

            # Ajouter la date de modification
            metadata["/ModDate"] = f"D:{datetime.now().strftime('%Y%m%d%H%M%S')}"

            pdf_writer.add_metadata(metadata)

            # Écrire le fichier final
            with open(output_path, "wb") as output_file:
                pdf_writer.write(output_file)

        # Nettoyer le fichier temporaire
        os.unlink(temp_file.name)

    def close_current_pdf(self):
        """Ferme le PDF actuel"""
        if self.pdf_document:
            self.pdf_document.close()
            self.pdf_document = None

        self.pdf_reader = None
        self.current_path = None
        self.total_pages = 0
        self.current_page = 0

    def __del__(self):
        """Nettoyage lors de la destruction"""
        self.close_current_pdf()
