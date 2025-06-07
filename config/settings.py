"""
Configuration et constantes de l'application
"""

# Configuration de l'interface
WINDOW_TITLE = "Éditeur PDF Avancé - Métadonnées et Contenu"
WINDOW_SIZE = "1400x900"
CANVAS_BG_COLOR = "white"

# Configuration du zoom
MIN_ZOOM = 0.5
MAX_ZOOM = 3.0
ZOOM_STEP = 0.25
DEFAULT_ZOOM = 1.0

# Configuration des couleurs
COLORS = {
    "black": (0, 0, 0),
    "red": (1, 0, 0),
    "blue": (0, 0, 1),
    "green": (0, 1, 0),
    "orange": (1, 0.5, 0),
    "yellow": (1, 1, 0),
    "pink": (1, 0.75, 0.8),
}

HIGHLIGHT_COLORS = ["yellow", "green", "blue", "pink", "orange"]
TEXT_COLORS = ["black", "red", "blue", "green", "orange"]

# Configuration des polices
DEFAULT_FONT_SIZE = 12
ROTATION_ANGLES = ["90", "180", "270"]

# Configuration des fichiers
SUPPORTED_FORMATS = [("Fichiers PDF", "*.pdf"), ("Tous les fichiers", "*.*")]
