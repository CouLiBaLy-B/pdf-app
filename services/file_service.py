"""
Service pour les opérations sur les fichiers
"""

from tkinter import filedialog, messagebox
import os


class FileService:
    @staticmethod
    def save_text(text_content):
        """Sauvegarde du texte dans un fichier"""
        file_path = filedialog.asksaveasfilename(
            title="Sauvegarder le texte extrait",
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")],
        )

        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text_content)
            messagebox.showinfo("Succès", f"Texte sauvegardé dans: {file_path}")

    @staticmethod
    def get_file_info(file_path):
        """Retourne les informations d'un fichier"""
        if not os.path.exists(file_path):
            return None

        return {
            "size": os.path.getsize(file_path),
            "name": os.path.basename(file_path),
            "path": file_path,
        }
