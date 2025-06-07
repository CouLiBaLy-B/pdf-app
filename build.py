"""
Script pour créer un exécutable avec PyInstaller
"""

import PyInstaller.__main__


def build_executable():
    """Crée l'exécutable"""

    # Options PyInstaller
    options = [
        "main.py",
        "--name=PDF_Editor",
        "--windowed",  # Pas de console
        "--onefile",  # Un seul fichier
        "--icon=assets/icon.ico",  # Icône (si disponible)
        "--add-data=config;config",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=fitz",
        "--hidden-import=PyPDF2",
        "--clean",
        "--noconfirm",
    ]

    print("Création de l'exécutable...")
    PyInstaller.__main__.run(options)
    print("Exécutable créé dans le dossier 'dist'")


if __name__ == "__main__":
    build_executable()
