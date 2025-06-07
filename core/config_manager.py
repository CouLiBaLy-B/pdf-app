"""
Gestionnaire de configuration utilisateur
"""

import json
import os
from pathlib import Path
from config.advanced_settings import UI_SETTINGS, PERFORMANCE_SETTINGS


class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".pdf_editor"
        self.config_file = self.config_dir / "config.json"
        self.config = self.load_config()

    def load_config(self):
        """Charge la configuration utilisateur"""
        default_config = {
            "ui": UI_SETTINGS.copy(),
            "performance": PERFORMANCE_SETTINGS.copy(),
            "recent_files": [],
            "window_geometry": None,
        }

        if not self.config_file.exists():
            return default_config

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                user_config = json.load(f)

            # Fusionner avec la config par défaut
            for key, value in default_config.items():
                if key not in user_config:
                    user_config[key] = value
                elif isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        if subkey not in user_config[key]:
                            user_config[key][subkey] = subvalue

            return user_config

        except Exception as e:
            print(f"Erreur lors du chargement de la config: {e}")
            return default_config

    def save_config(self):
        """Sauvegarde la configuration"""
        try:
            self.config_dir.mkdir(exist_ok=True)

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la config: {e}")

    def get(self, section, key, default=None):
        """Récupère une valeur de configuration"""
        return self.config.get(section, {}).get(key, default)

    def set(self, section, key, value):
        """Définit une valeur de configuration"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value

    def add_recent_file(self, file_path):
        """Ajoute un fichier à la liste des récents"""
        recent = self.config.get("recent_files", [])

        # Supprimer si déjà présent
        if file_path in recent:
            recent.remove(file_path)

        # Ajouter en tête
        recent.insert(0, file_path)

        # Limiter à 10 fichiers
        self.config["recent_files"] = recent[:10]

    def get_recent_files(self):
        """Retourne la liste des fichiers récents"""
        recent = self.config.get("recent_files", [])
        # Filtrer les fichiers qui n'existent plus
        return [f for f in recent if os.path.exists(f)]
