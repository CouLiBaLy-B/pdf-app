# Éditeur PDF Avancé

Un éditeur PDF complet avec interface graphique permettant l'édition de contenu, la gestion des métadonnées et la manipulation de documents PDF.

## Fonctionnalités

### Édition de Contenu

- Sélection et modification de texte
- Ajout de nouveau texte
- Surlignage et annotations
- Extraction de texte
- Navigation interactive

### Gestion des Métadonnées

- Modification des propriétés du document
- Titre, auteur, sujet, mots-clés
- Dates de création et modification

### Manipulation PDF

- Extraction de pages
- Fusion de documents
- Rotation de pages
- Informations détaillées

## Installation

1. Cloner le repository
2. Installer les dépendances : `pip install -r requirements.txt`
3. Lancer l'application : `python main.py`

## Structure du Projet

```md
pdf_editor/
├── main.py                     # Point d'entrée principal
├── main_updated.py             # Version améliorée avec nouvelles fonctionnalités
├── requirements.txt            # Dépendances
├── README.md                   # Documentation
├── INSTALL.md                  # Guide d'installation
├── build.py                    # Script de build
├── deploy.py                   # Script de déploiement
├── run.py                      # Lanceur avec gestion d'erreurs
├── config/
│   ├── __init__.py
│   ├── settings.py             # Configuration de base
│   └── advanced_settings.py    # Configuration avancée
├── core/
│   ├── __init__.py
│   ├── pdf_manager.py          # Gestionnaire PDF principal
│   └── config_manager.py       # Gestionnaire de configuration
├── ui/
│   ├── __init__.py
│   ├── tabs/
│   │   ├── __init__.py
│   │   ├── content_editor_tab.py    # Onglet d'édition
│   │   ├── metadata_tab.py          # Onglet métadonnées
│   │   ├── manipulation_tab.py      # Onglet manipulation
│   │   └── info_tab.py              # Onglet informations
│   └── components/
│       ├── __init__.py
│       ├── navigation_bar.py        # Barre de navigation
│       ├── tool_panels.py           # Panneaux d'outils
│       └── menu_bar.py              # Barre de menu
├── services/
│   ├── __init__.py
│   ├── text_service.py         # Service de texte
│   ├── annotation_service.py   # Service d'annotations
│   └── file_service.py         # Service de fichiers
├── utils/
│   ├── __init__.py
│   └── helpers.py              # Fonctions utilitaires
└── tests/
    ├── __init__.py
    ├── test_pdf_manager.py     # Tests du gestionnaire PDF
    ├── test_text_service.py    # Tests du service de texte
    └── test_integration.py     # Tests d'intégration
```

## Utilisation

1. Sélectionner un fichier PDF
2. Utiliser les onglets pour différentes fonctionnalités
3. Sauvegarder les modifications

## Dépendances

- PyPDF2 : Manipulation des métadonnées
- PyMuPDF : Édition de contenu
- Pillow : Traitement d'images
- tkinter : Interface graphique (inclus avec Python)
