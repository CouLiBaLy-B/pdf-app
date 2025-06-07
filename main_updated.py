"""
Version mise à jour du fichier principal avec toutes les améliorations
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

from core.pdf_manager import PDFManager
from core.config_manager import ConfigManager
from ui.tabs.content_editor_tab import ContentEditorTab
from ui.tabs.metadata_tab import MetadataTab
from ui.tabs.manipulation_tab import ManipulationTab
from ui.tabs.info_tab import InfoTab
from ui.components.menu_bar import MenuBar
from config.advanced_settings import KEYBOARD_SHORTCUTS


class PDFEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Éditeur PDF Avancé - v1.0")
        self.root.geometry("1400x900")

        # Gestionnaires
        self.config_manager = ConfigManager()
        self.pdf_manager = PDFManager()

        # Variables
        self.file_path_var = tk.StringVar()

        # Interface
        self.setup_ui()
        self.setup_keyboard_shortcuts()

        # Charger la géométrie sauvegardée
        self.load_window_geometry()

        # Gestionnaire de fermeture
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Menu
        self.menu_bar = MenuBar(self.root, self)

        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configuration du redimensionnement
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Section de sélection de fichier
        self.create_file_selection(main_frame)

        # Notebook pour les onglets
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10
        )
        main_frame.rowconfigure(2, weight=1)

        # Créer les onglets
        self.create_tabs()

        # Boutons d'action
        self.create_action_buttons(main_frame)

    def create_file_selection(self, parent):
        """Crée la section de sélection de fichier"""
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
        self.content_tab = ContentEditorTab(self.notebook, self.pdf_manager)
        self.metadata_tab = MetadataTab(self.notebook, self.pdf_manager)
        self.manipulation_tab = ManipulationTab(self.notebook, self.pdf_manager)
        self.info_tab = InfoTab(self.notebook, self.pdf_manager)

        # Liste des onglets pour les notifications
        self.tabs = [
            self.content_tab,
            self.metadata_tab,
            self.manipulation_tab,
            self.info_tab,
        ]

    def create_action_buttons(self, parent):
        """Crée les boutons d'action"""
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

    def setup_keyboard_shortcuts(self):
        """Configure les raccourcis clavier"""
        for action, shortcut in KEYBOARD_SHORTCUTS.items():
            if action == "open_file":
                self.root.bind(shortcut, lambda e: self.select_pdf())
            elif action == "save_file":
                self.root.bind(shortcut, lambda e: self.save_all_modifications())
            elif action == "save_as":
                self.root.bind(shortcut, lambda e: self.save_as())
            # Ajouter d'autres raccourcis selon les besoins

    def select_pdf(self):
        """Sélectionne un fichier PDF"""
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier PDF",
            filetypes=[("Fichiers PDF", "*.pdf"), ("Tous les fichiers", "*.*")],
        )

        if file_path:
            self.load_pdf_file(file_path)

    def load_pdf_file(self, file_path):
        """Charge un fichier PDF"""
        try:
            self.pdf_manager.load_pdf(file_path)
            self.file_path_var.set(file_path)

            # Ajouter aux fichiers récents
            self.config_manager.add_recent_file(file_path)
            self.config_manager.save_config()
            self.menu_bar.update_recent_menu()

            # Notifier tous les onglets
            for tab in self.tabs:
                if hasattr(tab, "on_pdf_loaded"):
                    tab.on_pdf_loaded()

            messagebox.showinfo("Succès", f"PDF chargé: {os.path.basename(file_path)}")

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger le PDF: {str(e)}")

    def save_all_modifications(self):
        """Sauvegarde toutes les modifications"""
        if not self.pdf_manager.current_path:
            messagebox.showwarning("Attention", "Aucun fichier PDF chargé")
            return

        try:
            # Récupérer les métadonnées de l'onglet
            metadata = self.metadata_tab.get_metadata()

            # Sauvegarder avec le gestionnaire PDF
            self.pdf_manager.save_with_metadata(metadata)

            # Recharger pour refléter les changements
            for tab in self.tabs:
                if hasattr(tab, "on_pdf_loaded"):
                    tab.on_pdf_loaded()

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
            filetypes=[("Fichiers PDF", "*.pdf")],
        )

        if output_path:
            try:
                metadata = self.metadata_tab.get_metadata()
                self.pdf_manager.save_as(output_path, metadata)

                messagebox.showinfo("Succès", f"PDF sauvegardé dans: {output_path}")

            except Exception as e:
                messagebox.showerror(
                    "Erreur", f"Erreur lors de la sauvegarde: {str(e)}"
                )

    def reset_form(self):
        """Réinitialise tous les champs"""
        if messagebox.askyesno("Confirmation", "Réinitialiser tous les champs?"):
            # Réinitialiser tous les onglets
            for tab in self.tabs:
                if hasattr(tab, "reset"):
                    tab.reset()

            # Réinitialiser le gestionnaire PDF
            self.pdf_manager.close_current_pdf()
            self.file_path_var.set("")

    def load_window_geometry(self):
        """Charge la géométrie de fenêtre sauvegardée"""
        geometry = self.config_manager.get("ui", "window_geometry")
        if geometry and self.config_manager.get("ui", "remember_geometry", True):
            try:
                self.root.geometry(geometry)
            except tk.TclError:
                pass  # Ignorer les erreurs de géométrie invalide

    def save_window_geometry(self):
        """Sauvegarde la géométrie de la fenêtre"""
        if self.config_manager.get("ui", "remember_geometry", True):
            self.config_manager.set("ui", "window_geometry", self.root.geometry())
            self.config_manager.save_config()

    def on_closing(self):
        """Gestionnaire de fermeture de l'application"""
        # Sauvegarder la géométrie
        self.save_window_geometry()

        # Fermer le PDF
        self.pdf_manager.close_current_pdf()

        # Fermer l'application
        self.root.destroy()


def main():
    """Fonction principale"""
    root = tk.Tk()
    app = PDFEditorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
