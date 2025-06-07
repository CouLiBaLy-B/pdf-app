"""
Onglet pour l'édition des métadonnées PDF
"""

import tkinter as tk
from tkinter import ttk


class MetadataTab:
    def __init__(self, notebook, pdf_manager):
        self.notebook = notebook
        self.pdf_manager = pdf_manager

        # Variables pour les métadonnées
        self.metadata_vars = {}

        self.create_tab()

    def create_tab(self):
        """Crée l'onglet métadonnées"""
        self.metadata_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.metadata_frame, text="Métadonnées")

        # Créer un canvas avec scrollbar
        canvas = tk.Canvas(self.metadata_frame)
        scrollbar = ttk.Scrollbar(
            self.metadata_frame, orient="vertical", command=canvas.yview
        )
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Champs de métadonnées
        self.create_metadata_fields(scrollable_frame)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_metadata_fields(self, parent):
        """Crée les champs de métadonnées"""
        metadata_fields = [
            ("Titre", "title"),
            ("Auteur", "author"),
            ("Sujet", "subject"),
            ("Créateur", "creator"),
            ("Producteur", "producer"),
            ("Mots-clés", "keywords"),
            ("Date de création", "creation_date"),
            ("Date de modification", "modification_date"),
        ]

        for i, (label, key) in enumerate(metadata_fields):
            ttk.Label(parent, text=f"{label}:").grid(
                row=i, column=0, sticky=tk.W, padx=5, pady=2
            )
            var = tk.StringVar()
            self.metadata_vars[key] = var
            ttk.Entry(parent, textvariable=var, width=50).grid(
                row=i, column=1, sticky=(tk.W, tk.E), padx=5, pady=2
            )

        parent.columnconfigure(1, weight=1)

    def get_metadata(self):
        """Retourne les métadonnées actuelles"""
        metadata = {}
        for key, var in self.metadata_vars.items():
            value = var.get().strip()
            if value:
                metadata[key] = value
        return metadata

    def load_metadata(self, metadata_dict):
        """Charge les métadonnées dans l'interface"""
        for key, var in self.metadata_vars.items():
            value = metadata_dict.get(key, "")
            var.set(value)

    def on_pdf_loaded(self):
        """Appelé quand un nouveau PDF est chargé"""
        if self.pdf_manager.pdf_document:
            metadata = self.pdf_manager.get_metadata()
            self.load_metadata(metadata)

    def reset(self):
        """Réinitialise tous les champs"""
        for var in self.metadata_vars.values():
            var.set("")
