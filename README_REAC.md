# Éditeur PDF Avancé

Un éditeur PDF complet avec interface web moderne permettant l'édition de contenu, la manipulation de documents et la gestion des métadonnées.

## 🚀 Fonctionnalités

### Édition de Contenu

- ✅ Sélection et édition de texte
- ✅ Ajout de nouveau texte
- ✅ Suppression et remplacement de texte
- ✅ Surlignage avec différentes couleurs
- ✅ Ajout de notes et annotations
- ✅ Préservation du formatage original

### Manipulation de Documents

- ✅ Extraction de pages spécifiques
- ✅ Fusion de plusieurs PDFs
- ✅ Rotation de pages
- ✅ Compression de documents
- ✅ Division de documents

### Gestion des Métadonnées

- ✅ Édition des propriétés du document
- ✅ Mise à jour des dates
- ✅ Gestion des mots-clés
- ✅ Statistiques du document

### Interface Utilisateur

- ✅ Interface moderne et responsive
- ✅ Navigation intuitive par onglets
- ✅ Zoom et navigation des pages
- ✅ Glisser-déposer pour l'upload
- ✅ Fichiers récents
- ✅ Notifications en temps réel

## 🛠️ Technologies Utilisées

### Frontend

- **HTML5/CSS3** - Structure et style moderne
- **JavaScript ES6+** - Logique applicative
- **PDF.js** - Rendu et manipulation PDF côté client
- **Font Awesome** - Icônes
- **CSS Grid/Flexbox** - Layout responsive

### Backend

- **Node.js** - Serveur JavaScript
- **Express.js** - Framework web
- **PDF-lib** - Manipulation PDF avancée
- **Multer** - Upload de fichiers
- **PDFKit** - Génération de PDF

### DevOps

- **Docker** - Conteneurisation
- **Nginx** - Proxy inverse et SSL
- **Jest** - Tests unitaires

## 📦 Installation

### Prérequis

- Node.js 18+
- npm ou yarn
- Docker (optionnel)

### Installation locale

1. **Cloner le repository**

```bash
git clone https://github.com/votre-username/pdf-editor.git
cd pdf-editor
```

2. **Installer les dépendances**

```bash
cd server
npm install
```

3. **Démarrer le serveur**

```bash
npm start
```

4. **Accéder à l'application**
Ouvrir <http://localhost:3000> dans votre navigateur

### Installation avec Docker

1. **Construire et démarrer**

```bash
docker-compose up -d
```

2. **Accéder à l'application**
Ouvrir <http://localhost> dans votre navigateur

## 🎯 Utilisation

### Chargement d'un PDF

1. Glissez-déposez un fichier PDF ou cliquez sur "Choisir un fichier"
2. Le PDF s'affiche automatiquement dans l'éditeur

### Édition de Texte

1. Sélectionnez le mode "Sélection"
2. Cliquez et glissez pour sélectionner du texte
3. Utilisez les outils dans le panneau de droite pour :
   - Supprimer le texte
   - Le remplacer
   - Le copier
   - Le surligner

### Ajout de Texte

1. Sélectionnez le mode "Texte"
2. Cliquez à l'endroit désiré
3. Saisissez le texte dans le panneau d'outils
4. Configurez la taille et la couleur
5. Cliquez "Ajouter Texte"

### Manipulation de Documents

1. Allez dans l'onglet "Manipulation"
2. Choisissez l'opération désirée :
   - **Extraction** : Spécifiez les pages (ex: 1,3,5-7)
   - **Fusion** : Ajoutez plusieurs fichiers PDF
   - **Rotation** : Sélectionnez pages et angle
   - **Compression** : Choisissez le niveau

### Métadonnées

1. Allez dans l'onglet "Métadonnées"
2. Modifiez les champs désirés
3. Cliquez "Sauvegarder les métadonnées"

## 🔧 Configuration

### Variables d'environnement

```bash
NODE_ENV=production
PORT=3000
MAX_FILE_SIZE=50MB
UPLOAD_DIR=./uploads
```

### Configuration SSL (production)

Placez vos certificats dans le dossier `ssl/` :

- `cert.pem` - Certificat SSL
- `key.pem` - Clé privée

## 🧪 Tests

```bash
cd server
npm test
```

## 📝 API Documentation

### Endpoints principaux

#### POST /api/extract-pages

Extrait des pages spécifiques d'un PDF.

**Paramètres :**

- `pdf` (file) - Fichier PDF
- `pages` (array) - Numéros des pages à extraire

#### POST /api/merge-pdfs

Fusionne plusieurs fichiers PDF.

**Paramètres :**

- `pdfs` (files) - Fichiers PDF à fusionner

#### POST /api/rotate-pages

Applique une rotation aux pages spécifiées.

**Paramètres :**

- `pdf` (file) - Fichier PDF
- `pages` (array) - Pages à faire tourner
- `angle` (number) - Angle de rotation (90, 180, 270)

#### POST /api/save-pdf

Sauvegarde un PDF avec toutes les modifications.

**Paramètres :**

- `pdf` (file) - Fichier PDF original
- `modifications` (array) - Liste des modifications à appliquer

## 🤝 Contribution

1. Fork le projet
2. Créez une branche feature (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🐛 Signaler un Bug

Utilisez les [GitHub Issues](https://github.com/votre-username/pdf-editor/issues) pour signaler des bugs ou demander des fonctionnalités.

## 📞 Support

- 📧 Email: support@pdf-editor.com
- 💬 Discord: [Serveur communautaire](https://discord.gg/pdf-editor)
- 📖 Wiki: [Documentation complète](https://github.com/votre-username/pdf-editor/wiki)

## 🔄 Changelog

### v1.0.0 (2024-01-15)
- ✨ Version initiale
- ✅ Édition de texte complète
- ✅ Manipulation de documents
- ✅ Interface utilisateur moderne
- ✅ Support Docker

### v0.9.0 (2024-01-10)
- 🔧 Version bêta
- ✅ Fonctionnalités de base
- 🧪 Tests unitaires

## 🚀 Roadmap

### v1.1.0 (Q2 2024)
- [ ] Édition d'images dans les PDFs
- [ ] OCR pour les PDFs scannés
- [ ] Signatures électroniques
- [ ] Templates de documents

### v1.2.0 (Q3 2024)
- [ ] Collaboration en temps réel
- [ ] Historique des versions
- [ ] API REST complète
- [ ] Plugin système

### v2.0.0 (Q4 2024)
- [ ] Interface mobile native
- [ ] Intelligence artificielle
- [ ] Cloud storage intégré
- [ ] Workflow automation

## 🏗️ Architecture

```
pdf-editor/
├── public/                 # Frontend
│   ├── index.html         # Page principale
│   ├── styles.css         # Styles CSS
│   ├── app.js            # Application JavaScript
│   └── assets/           # Images et ressources
├── server/               # Backend
│   ├── server.js         # Serveur Express
│   ├── package.json      # Dépendances Node.js
│   └── tests/           # Tests unitaires
├── docker-compose.yml    # Configuration Docker
├── Dockerfile           # Image Docker
├── nginx.conf          # Configuration Nginx
└── README.md          # Documentation
```

## 🔒 Sécurité

### Mesures de sécurité implémentées
- ✅ Validation des fichiers uploadés
- ✅ Limitation de taille des fichiers (50MB)
- ✅ Headers de sécurité HTTP
- ✅ Protection CSRF
- ✅ Sanitisation des entrées
- ✅ HTTPS obligatoire en production

### Signaler une vulnérabilité
Envoyez un email à security@pdf-editor.com pour signaler des problèmes de sécurité.

## 📊 Performance

### Benchmarks
- **Chargement PDF** : < 2s pour fichiers de 10MB
- **Rendu page** : < 500ms
- **Sauvegarde** : < 3s pour modifications complexes
- **Mémoire** : < 100MB pour documents standards

### Optimisations
- Rendu lazy des pages
- Compression automatique des images
- Cache intelligent
- Streaming des gros fichiers

## 🌍 Internationalisation

Langues supportées :
- 🇫🇷 Français (par défaut)
- 🇺🇸 Anglais
- 🇪🇸 Espagnol
- 🇩🇪 Allemand

Pour ajouter une langue :
1. Créez un fichier `public/locales/[code].json`
2. Traduisez toutes les clés
3. Ajoutez la langue dans `app.js`

## 🧩 Extensions

### Plugins disponibles
- **PDF-OCR** : Reconnaissance de texte
- **PDF-Sign** : Signatures électroniques
- **PDF-Forms** : Édition de formulaires
- **PDF-Watermark** : Filigranes

### Créer un plugin
```javascript
// plugin-example.js
class PDFPlugin {
    constructor(editor) {
        this.editor = editor;
    }
    
    init() {
        // Initialisation du plugin
    }
    
    process(pdf) {
        // Traitement du PDF
        return pdf;
    }
}

// Enregistrer le plugin
window.pdfEditor.registerPlugin('example', PDFPlugin);
```

## 📱 Compatibilité

### Navigateurs supportés
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ❌ Internet Explorer (non supporté)

### Appareils
- 💻 Desktop (Windows, macOS, Linux)
- 📱 Mobile (iOS 14+, Android 10+)
- 📟 Tablettes (iPad, Android tablets)

## 🔧 Développement

### Prérequis développeur
```bash
# Installer les outils de développement
npm install -g nodemon
npm install -g jest
npm install -g eslint
```

### Scripts de développement
```bash
# Développement avec rechargement automatique
npm run dev

# Tests avec surveillance
npm run test:watch

# Linting du code
npm run lint

# Build de production
npm run build

# Analyse de sécurité
npm audit
```

### Structure du code
```javascript
// Conventions de nommage
class PDFEditor {           // PascalCase pour les classes
    constructor() {
        this.currentPage = 1;   // camelCase pour les propriétés
    }
    
    renderPage() {          // camelCase pour les méthodes
        // Implementation
    }
}

// Constants en UPPER_CASE
const MAX_FILE_SIZE = 50 * 1024 * 1024;
```

## 🎨 Personnalisation

### Thèmes
Modifiez les variables CSS dans `styles.css` :
```css
:root {
    --primary-color: #3b82f6;
    --secondary-color: #64748b;
    --background-color: #f8fafc;
    --text-color: #1e293b;
    --border-radius: 8px;
    --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
```

### Interface personnalisée
```javascript
// Configuration de l'interface
const config = {
    theme: 'dark',
    language: 'fr',
    toolbar: {
        position: 'top',
        items: ['open', 'save', 'zoom', 'pages']
    },
    panels: {
        tools: true,
        properties: true,
        preview: false
    }
};

window.pdfEditor.configure(config);
```

## 📈 Monitoring

### Métriques collectées
- Temps de chargement des PDFs
- Nombre d'opérations par session
- Erreurs et exceptions
- Utilisation mémoire
- Taille des fichiers traités

### Intégration monitoring
```javascript
// Google Analytics
gtag('event', 'pdf_loaded', {
    'file_size': fileSize,
    'load_time': loadTime
});

// Sentry pour les erreurs
Sentry.captureException(error);
```

## 🔄 Migration

### Depuis la version 0.x
1. Sauvegardez vos données
2. Mettez à jour le code
3. Exécutez les migrations :
```bash
npm run migrate
```

### Format des données
Les modifications sont stockées au format JSON :
```json
{
    "version": "1.0",
    "modifications": [
        {
            "type": "text",
            "page": 1,
            "data": {
                "text": "Nouveau texte",
                "x": 100,
                "y": 200,
                "fontSize": 12,
                "color": "#000000"
            }
        }
    ]
}
```

## 🤖 Automatisation

### Scripts utiles
```bash
#!/bin/bash
# deploy.sh - Script de déploiement
set -e

echo "🚀 Déploiement en cours..."

# Tests
npm test

# Build
npm run build

# Docker
docker-compose down
docker-compose up -d --build

echo "✅ Déploiement terminé"
```

### GitHub Actions
```yaml
# .github/workflows/ci.yml
name: CI/CD

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    - name: Install dependencies
      run: npm ci
    - name: Run tests
      run: npm test
    - name: Build
      run: npm run build
```

## 📚 Ressources

### Documentation technique
- [PDF.js Documentation](https://mozilla.github.io/pdf.js/)
- [PDF-lib Guide](https://pdf-lib.js.org/)
- [Express.js Documentation](https://expressjs.com/)

### Tutoriels
- [Manipulation PDF avec JavaScript](https://example.com/tutorial-1)
- [Interface utilisateur moderne](https://example.com/tutorial-2)
- [Déploiement Docker](https://example.com/tutorial-3)

### Communauté
- 💬 [Forum de discussion](https://forum.pdf-editor.com)
- 📺 [Chaîne YouTube](https://youtube.com/pdf-editor)
- 🐦 [Twitter](https://twitter.com/pdf_editor)

---

**Fait avec ❤️ par l'équipe PDF Editor**

*Dernière mise à jour : 15 janvier 2024*

