"""
Fenêtre principale de l'éditeur PDF
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from config.settings import WINDOW_TITLE, WINDOW_SIZE, SUPPORTED_FORMATS
from core.pdf_manager import PDFManager
from ui.tabs.content_editor_tab import ContentEditorTab
from ui.tabs.metadata_tab import MetadataTab
from ui.tabs.manipulation_tab import ManipulationTab
from ui.tabs.info_tab import InfoTab


class PDFEditorMainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        self.root.geometry(WINDOW_SIZE)

        # Gestionnaire PDF
        self.pdf_manager = PDFManager()

        # Variables d'interface
        self.file_path_var = tk.StringVar()

        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configuration du redimensionnement
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Section de sélection de fichier
        self.setup_file_selection(main_frame)

        # Notebook pour les onglets
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10
        )
        main_frame.rowconfigure(2, weight=1)

        # Créer les onglets
        self.create_tabs()

        # Boutons d'action
        self.setup_action_buttons(main_frame)

    def setup_file_selection(self, parent):
        """Configure la section de sélection de fichier"""
        ttk.Label(parent, text="Fichier PDF:", font=("Arial", 12, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )

        file_frame = ttk.Frame(parent)
        file_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        file_frame.columnconfigure(0, weight=1)

        ttk.Entry(file_frame, textvariable=self.file_path_var, state="readonly").grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5)
        )
        ttk.Button(file_frame, text="Parcourir", command=self.select_pdf).grid(
            row=0, column=1
        )

    def create_tabs(self):
        """Crée tous les onglets"""
        # Onglet éditeur de contenu
        self.content_tab = ContentEditorTab(self.notebook, self.pdf_manager)

        # Onglet métadonnées
        self.metadata_tab = MetadataTab(self.notebook, self.pdf_manager)

        # Onglet manipulation
        self.manipulation_tab = ManipulationTab(self.notebook, self.pdf_manager)

        # Onglet informations
        self.info_tab = InfoTab(self.notebook, self.pdf_manager)

    def setup_action_buttons(self, parent):
        """Configure les boutons d'action"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(
            button_frame,
            text="Sauvegarder toutes les modifications",
            command=self.save_all_modifications,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Sauvegarder sous...", command=self.save_as).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Réinitialiser", command=self.reset_form).pack(
            side=tk.LEFT, padx=5
        )

    def select_pdf(self):
        """Sélectionne un fichier PDF"""
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier PDF", filetypes=SUPPORTED_FORMATS
        )

        if file_path:
            try:
                self.pdf_manager.load_pdf(file_path)
                self.file_path_var.set(file_path)

                # Notifier tous les onglets du nouveau PDF
                self.content_tab.on_pdf_loaded()
                self.metadata_tab.on_pdf_loaded()
                self.manipulation_tab.on_pdf_loaded()
                self.info_tab.on_pdf_loaded()

            except Exception as e:
                messagebox.showerror("Erreur", str(e))

    def save_all_modifications(self):
        """Sauvegarde toutes les modifications"""
        if not self.pdf_manager.current_path:
            messagebox.showwarning("Attention", "Aucun fichier PDF chargé")
            return

        try:
            # Récupérer les métadonnées depuis l'onglet
            metadata = self.metadata_tab.get_metadata()

            # Sauvegarder
            self.pdf_manager.save_with_metadata(self.pdf_manager.current_path, metadata)

            # Recharger
            self.pdf_manager.load_pdf(self.pdf_manager.current_path)
            self.content_tab.on_pdf_loaded()
            self.metadata_tab.on_pdf_loaded()
            self.info_tab.on_pdf_loaded()

            messagebox.showinfo(
                "Succès", "Toutes les modifications ont été sauvegardées!"
            )

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde: {str(e)}")

    def save_as(self):
        """Sauvegarde sous un nouveau nom"""
        if not self.pdf_manager.current_path:
            messagebox.showwarning("Attention", "Aucun fichier PDF chargé")
            return

        output_path = filedialog.asksaveasfilename(
            title="Sauvegarder sous...",
            defaultextension=".pdf",
            filetypes=SUPPORTED_FORMATS,
        )

        if output_path:
            try:
                metadata = self.metadata_tab.get_metadata()
                self.pdf_manager.save_with_metadata(output_path, metadata)
                messagebox.showinfo("Succès", f"PDF sauvegardé dans: {output_path}")
            except Exception as e:
                messagebox.showerror(
                    "Erreur", f"Erreur lors de la sauvegarde: {str(e)}"
                )

    def reset_form(self):
        """Réinitialise tous les champs"""
        # Réinitialiser tous les onglets
        self.content_tab.reset()
        self.metadata_tab.reset()
        self.manipulation_tab.reset()
        self.info_tab.reset()

        # Fermer le PDF
        self.pdf_manager.close_current_pdf()
        self.file_path_var.set("")

    def cleanup(self):
        """Nettoyage lors de la fermeture"""
        self.pdf_manager.close_current_pdf()
