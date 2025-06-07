"""
Script de lancement alternatif avec gestion d'erreurs
"""

import tkinter as tk
from tkinter import messagebox
import traceback


def check_dependencies():
    """Vérifie que toutes les dépendances sont installées"""
    missing_deps = []

    try:
        import PyPDF2
    except ImportError:
        missing_deps.append("PyPDF2")

    try:
        import fitz
    except ImportError:
        missing_deps.append("PyMuPDF")

    try:
        from PIL import Image, ImageTk
    except ImportError:
        missing_deps.append("Pillow")

    return missing_deps


def main():
    """Fonction principale avec gestion d'erreurs"""
    try:
        # Vérifier les dépendances
        missing = check_dependencies()
        if missing:
            root = tk.Tk()
            root.withdraw()  # Cacher la fenêtre principale
            messagebox.showerror(
                "Dépendances manquantes",
                f"Les modules suivants sont requis:\n{', '.join(missing)}\n\n"
                f"Installez-les avec: pip install {' '.join(missing)}",
            )
            return

        # Importer et lancer l'application
        from main import main as app_main

        app_main()

    except Exception as e:
        # Afficher l'erreur dans une boîte de dialogue
        root = tk.Tk()
        root.withdraw()

        error_msg = (
            f"Erreur lors du lancement:\n{str(e)}\n\nDétails:\n{traceback.format_exc()}"
        )
        messagebox.showerror("Erreur", error_msg)

        print("Erreur détaillée:")
        traceback.print_exc()


if __name__ == "__main__":
    main()
