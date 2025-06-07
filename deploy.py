"""
Script de déploiement et packaging
"""

import os
import shutil
import zipfile
from pathlib import Path
import subprocess


def create_distribution():
    """Crée une distribution complète de l'application"""

    # Dossiers et fichiers à inclure
    include_dirs = ["config", "core", "ui", "services", "utils"]
    include_files = ["main.py", "requirements.txt", "README.md", "INSTALL.md"]

    # Créer le dossier de distribution
    dist_dir = Path("dist_package")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir()

    # Copier les dossiers
    for dir_name in include_dirs:
        if os.path.exists(dir_name):
            shutil.copytree(dir_name, dist_dir / dir_name)

    # Copier les fichiers
    for file_name in include_files:
        if os.path.exists(file_name):
            shutil.copy2(file_name, dist_dir / file_name)

    # Créer le script d'installation
    create_install_script(dist_dir)

    # Créer l'archive ZIP
    create_zip_archive(dist_dir)

    print("Distribution créée avec succès!")


def create_install_script(dist_dir):
    """Crée un script d'installation automatique"""

    install_script = """#!/usr/bin/env python3
\"\"\"
Script d'installation automatique pour l'Éditeur PDF
\"\"\"
import subprocess
import sys
import os

def install():
    print("=== Installation de l'Éditeur PDF Avancé ===")

    # Vérifier Python
    if sys.version_info < (3, 7):
        print("ERREUR: Python 3.7 ou supérieur requis")
        return False

    try:
        # Installer les dépendances
        print("Installation des dépendances...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])

        print("Installation terminée avec succès!")
        print("Lancez l'application avec: python main.py")
        return True

    except subprocess.CalledProcessError as e:
        print(f"ERREUR lors de l'installation: {e}")
        return False

if __name__ == "__main__":
    success = install()
    if not success:
        input("Appuyez sur Entrée pour fermer...")
        sys.exit(1)
"""

    with open(dist_dir / "install.py", "w", encoding="utf-8") as f:
        f.write(install_script)


def create_zip_archive(dist_dir):
    """Crée une archive ZIP de la distribution"""

    zip_name = "PDF_Editor_v1.0.zip"

    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, dist_dir.parent)
                zipf.write(file_path, arc_name)

    print(f"Archive créée: {zip_name}")


def run_tests():
    """Lance tous les tests avant le déploiement"""
    print("Lancement des tests...")

    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-v"], capture_output=True, text=True
        )

        if result.returncode == 0:
            print("✓ Tous les tests passent")
            return True
        else:
            print("✗ Certains tests échouent:")
            print(result.stdout)
            print(result.stderr)
            return False

    except FileNotFoundError:
        print("pytest non trouvé, tests ignorés")
        return True


def main():
    """Fonction principale de déploiement"""
    print("=== Script de déploiement ===")

    # Lancer les tests
    if not run_tests():
        if input("Tests échoués. Continuer? (y/N): ").lower() != "y":
            return

    # Créer la distribution
    create_distribution()

    print("Déploiement terminé!")


if __name__ == "__main__":
    main()
