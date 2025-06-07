"""
Barre de menu avec fichiers récents
"""

import tkinter as tk
from tkinter import messagebox
import os


class MenuBar:
    def __init__(self, root, main_window):
        self.root = root
        self.main_window = main_window
        self.config_manager = main_window.config_manager

        self.create_menu()

    def create_menu(self):
        """Crée la barre de menu"""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # Menu Fichier
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Fichier", menu=self.file_menu)

        self.file_menu.add_command(
            label="Ouvrir...", command=self.main_window.select_pdf, accelerator="Ctrl+O"
        )

        # Sous-menu fichiers récents
        self.recent_menu = tk.Menu(self.file_menu, tearoff=0)
        self.file_menu.add_cascade(label="Fichiers récents", menu=self.recent_menu)
        self.update_recent_menu()

        self.file_menu.add_separator()
        self.file_menu.add_command(
            label="Sauvegarder",
            command=self.main_window.save_all_modifications,
            accelerator="Ctrl+S",
        )
        self.file_menu.add_command(
            label="Sauvegarder sous...",
            command=self.main_window.save_as,
            accelerator="Ctrl+Shift+S",
        )

        self.file_menu.add_separator()
        self.file_menu.add_command(label="Quitter", command=self.quit_app)

        # Menu Édition
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Édition", menu=edit_menu)
        edit_menu.add_command(
            label="Réinitialiser", command=self.main_window.reset_form
        )

        # Menu Affichage
        view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Affichage", menu=view_menu)
        view_menu.add_command(label="Zoom +", accelerator="Ctrl++")
        view_menu.add_command(label="Zoom -", accelerator="Ctrl+-")

        # Menu Aide
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="À propos", command=self.show_about)

    def update_recent_menu(self):
        """Met à jour le menu des fichiers récents"""
        self.recent_menu.delete(0, tk.END)

        recent_files = self.config_manager.get_recent_files()

        if not recent_files:
            self.recent_menu.add_command(label="Aucun fichier récent", state="disabled")
        else:
            for file_path in recent_files:
                filename = os.path.basename(file_path)
                self.recent_menu.add_command(
                    label=filename,
                    command=lambda path=file_path: self.open_recent_file(path),
                )

            self.recent_menu.add_separator()
            self.recent_menu.add_command(
                label="Effacer la liste", command=self.clear_recent_files
            )

    def open_recent_file(self, file_path):
        """Ouvre un fichier récent"""
        if os.path.exists(file_path):
            self.main_window.load_pdf_file(file_path)
        else:
            messagebox.showerror("Erreur", f"Le fichier n'existe plus:\n{file_path}")
            # Supprimer de la liste des récents
            recent = self.config_manager.config.get("recent_files", [])
            if file_path in recent:
                recent.remove(file_path)
                self.config_manager.save_config()
                self.update_recent_menu()

    def clear_recent_files(self):
        """Efface la liste des fichiers récents"""
        self.config_manager.config["recent_files"] = []
        self.config_manager.save_config()
        self.update_recent_menu()

    def show_about(self):
        """Affiche la boîte À propos"""
        about_text = """Éditeur PDF Avancé
Version 1.0

Un éditeur PDF complet avec interface graphique.

Fonctionnalités:
• Édition de contenu et métadonnées
• Manipulation de documents
• Annotations et surlignage
• Extraction de texte

Développé avec Python et tkinter
© 2024"""

        messagebox.showinfo("À propos", about_text)

    def quit_app(self):
        """Quitte l'application"""
        if messagebox.askokcancel("Quitter", "Voulez-vous vraiment quitter?"):
            self.main_window.on_closing()
