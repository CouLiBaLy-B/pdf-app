# Guide d'installation - Éditeur PDF Avancé

## Prérequis

- Python 3.7 ou supérieur
- pip (gestionnaire de paquets Python)

## Installation depuis les sources

### 1. Cloner ou télécharger le projet

```bash
git clone https://github.com/votre-repo/pdf-editor.git
cd pdf-editor
```

### 2. Créer un environnement virtuel (recommandé)

```bash
# Windows
python -m venv pdf_editor_env
pdf_editor_env\Scripts\activate

# Linux/Mac
python3 -m venv pdf_editor_env
source pdf_editor_env/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Lancer l'application

```bash
python main.py
```

## Installation des dépendances manuellement

Si le fichier requirements.txt n'est pas disponible :

```bash
pip install PyPDF2==3.0.1
pip install PyMuPDF==1.23.5
pip install Pillow==10.0.1
```

## Création d'un exécutable

Pour créer un exécutable standalone :

```bash
pip install pyinstaller
python build.py
```

L'exécutable sera créé dans le dossier `dist/`.

## Résolution des problèmes

### Erreur "Module not found"

- Vérifiez que toutes les dépendances sont installées
- Activez l'environnement virtuel si vous en utilisez un
- Réinstallez les dépendances : `pip install -r requirements.txt --force-reinstall`

### Erreur avec PyMuPDF

- Sur certains systèmes, installez avec : `pip install --upgrade pymupdf`
- Ou essayez : `pip install fitz`

### Problèmes d'affichage

- Vérifiez que Pillow est correctement installé
- Sur Linux, installez les dépendances système : `sudo apt-get install python3-tk`

### Erreurs de permissions

- Sur Windows, lancez en tant qu'administrateur
- Sur Linux/Mac, vérifiez les permissions du dossier

## Configuration

L'application crée automatiquement un dossier de configuration dans :

- Windows : `C:\Users\[utilisateur]\.pdf_editor\`
- Linux/Mac : `~/.pdf_editor/`

Ce dossier contient :

- `config.json` : Paramètres utilisateur
- Fichiers de sauvegarde automatique (si activés)

## Désinstallation

1. Supprimez le dossier de l'application
2. Supprimez le dossier de configuration utilisateur
3. Désactivez et supprimez l'environnement virtuel (si utilisé)
