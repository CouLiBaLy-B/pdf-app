"""
Configuration avancée de l'application
"""

# Paramètres de performance
PERFORMANCE_SETTINGS = {
    "max_image_size": (2000, 2000),  # Taille max des images affichées
    "cache_pages": True,  # Cache des pages rendues
    "max_cached_pages": 10,  # Nombre max de pages en cache
    "render_quality": 150,  # DPI pour le rendu
}

# Paramètres d'interface
UI_SETTINGS = {
    "theme": "default",  # Thème de l'interface
    "font_family": "Arial",  # Police par défaut
    "font_size": 9,  # Taille de police
    "window_state": "normal",  # État initial de la fenêtre
    "remember_geometry": True,  # Mémoriser la taille/position
}

# Paramètres de sauvegarde
SAVE_SETTINGS = {
    "auto_backup": True,  # Sauvegarde automatique
    "backup_interval": 300,  # Intervalle en secondes
    "max_backups": 5,  # Nombre max de sauvegardes
    "compress_output": False,  # Compression des PDF de sortie
}

# Raccourcis clavier
KEYBOARD_SHORTCUTS = {
    "open_file": "<Control-o>",
    "save_file": "<Control-s>",
    "save_as": "<Control-Shift-s>",
    "zoom_in": "<Control-plus>",
    "zoom_out": "<Control-minus>",
    "next_page": "<Control-Right>",
    "prev_page": "<Control-Left>",
    "first_page": "<Control-Home>",
    "last_page": "<Control-End>",
}
