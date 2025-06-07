"""
Onglet d'affichage des informations PDF
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import os
from utils.helpers import format_file_size


class InfoTab:
    def __init__(self, notebook, pdf_manager):
        self.notebook = notebook
        self.pdf_manager = pdf_manager

        self.create_tab()

    def create_tab(self):
        """Crée l'onglet informations"""
        self.info_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.info_frame, text="Informations")

        self.info_text = scrolledtext.ScrolledText(
            self.info_frame, wrap=tk.WORD, height=20
        )
        self.info_text.pack(fill="both", expand=True, padx=10, pady=10)

    def display_pdf_info(self):
        """Affiche les informations du PDF"""
        if not self.pdf_manager.current_path:
            return

        info_text = (
            f"Informations du PDF: {os.path.basename(self.pdf_manager.current_path)}\n"
        )
        info_text += "=" * 50 + "\n\n"

        # Informations générales
        info_text += f"Nombre de pages: {self.pdf_manager.total_pages}\n"

        if os.path.exists(self.pdf_manager.current_path):
            file_size = os.path.getsize(self.pdf_manager.current_path)
            info_text += f"Taille du fichier: {format_file_size(file_size)}\n"

        # Métadonnées
        metadata = self.pdf_manager.get_metadata()
        if metadata:
            info_text += "\nMétadonnées:\n"
            info_text += "-" * 20 + "\n"
            for key, value in metadata.items():
                if value:
                    info_text += f"{key.capitalize()}: {value}\n"

        # Informations sur les pages (limité aux 5 premières)
        if self.pdf_manager.pdf_document:
            info_text += "\nInformations des pages:\n"
            info_text += "-" * 30 + "\n"

            max_pages_to_show = min(5, self.pdf_manager.total_pages)
            for i in range(max_pages_to_show):
                try:
                    page = self.pdf_manager.pdf_document[i]
                    rect = page.rect
                    info_text += (
                        f"Page {i+1}: {rect.width:.1f} x {rect.height:.1f} pts\n"
                    )
                except Exception:
                    info_text += f"Page {i+1}: Impossible de lire les dimensions\n"

            if self.pdf_manager.total_pages > 5:
                info_text += f"... et {self.pdf_manager.total_pages - 5} autres pages\n"

        self.info_text.delete("1.0", tk.END)
        self.info_text.insert("1.0", info_text)

    def on_pdf_loaded(self):
        """Appelé quand un nouveau PDF est chargé"""
        self.display_pdf_info()

    def reset(self):
        """Réinitialise l'onglet"""
        self.info_text.delete("1.0", tk.END)
