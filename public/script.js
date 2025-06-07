class PDFApp {
    constructor() {
        this.selectedFiles = [];
        this.selectedTool = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
    }

    setupEventListeners() {
        // File input
        const fileInput = document.getElementById('fileInput');
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

        // Tool cards
        const toolCards = document.querySelectorAll('.tool-card');
        toolCards.forEach(card => {
            card.addEventListener('click', (e) => this.selectTool(e));
        });

        // Action buttons
        document.getElementById('processBtn').addEventListener('click', () => this.processFiles());
        document.getElementById('clearBtn').addEventListener('click', () => this.clearFiles());

        // Upload area click
        document.getElementById('uploadArea').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    }

    setupDragAndDrop() {
        const uploadArea = document.getElementById('uploadArea');

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, () => {
                uploadArea.classList.remove('dragover');
            }, false);
        });

        uploadArea.addEventListener('drop', (e) => this.handleDrop(e), false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        this.handleFiles(files);
    }

    handleFileSelect(e) {
        const files = e.target.files;
        this.handleFiles(files);
    }

    handleFiles(files) {
        const fileArray = Array.from(files);
        const pdfFiles = fileArray.filter(file => file.type === 'application/pdf');

        if (pdfFiles.length === 0) {
            this.showNotification('Veuillez sélectionner des fichiers PDF valides.', 'warning');
            return;
        }

        this.selectedFiles = [...this.selectedFiles, ...pdfFiles];
        this.displayFiles();
        this.showSection('filesSection');
    }

    displayFiles() {
        const filesList = document.getElementById('filesList');
        filesList.innerHTML = '';

        this.selectedFiles.forEach((file, index) => {
            const fileItem = this.createFileItem(file, index);
            filesList.appendChild(fileItem);
        });
    }

    createFileItem(file, index) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item fade-in';
        
        const fileSize = this.formatFileSize(file.size);
        
        fileItem.innerHTML = `
            <div class="file-info">
                <div class="file-icon">
                    <i class="fas fa-file-pdf"></i>
                </div>
                <div class="file-details">
                    <h4>${file.name}</h4>
                    <p>${fileSize} • PDF</p>
                </div>
            </div>
            <div class="file-actions">
                <button class="btn btn-secondary btn-small" onclick="app.removeFile(${index})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        return fileItem;
    }

    removeFile(index) {
        this.selectedFiles.splice(index, 1);
        this.displayFiles();
        
        if (this.selectedFiles.length === 0) {
            this.hideSection('filesSection');
        }
    }

    selectTool(e) {
        const toolCard = e.currentTarget;
        const tool = toolCard.dataset.tool;

        // Remove active class from all cards
        document.querySelectorAll('.tool-card').forEach(card => {
            card.classList.remove('active');
        });

        // Add active class to selected card
        toolCard.classList.add('active');
        this.selectedTool = tool;

        this.showNotification(`Outil "${this.getToolName(tool)}" sélectionné`, 'success');
    }

    getToolName(tool) {
        const toolNames = {
            'merge': 'Fusionner',
            'split': 'Diviser',
            'compress': 'Compresser',
            'convert': 'Convertir'
        };
        return toolNames[tool] || tool;
    }

    async processFiles() {
        if (this.selectedFiles.length === 0) {
            this.showNotification('Veuillez sélectionner au moins un fichier.', 'warning');
            return;
        }

        if (!this.selectedTool) {
            this.showNotification('Veuillez sélectionner un outil.', 'warning');
            return;
        }

        this.showSection('progressSection');
        this.showLoadingOverlay();

        try {
            const formData = new FormData();
            this.selectedFiles.forEach(file => {
                formData.append('files', file);
            });
            formData.append('tool', this.selectedTool);

            const response = await fetch('/api/process', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Erreur lors du traitement des fichiers');
            }

            const result = await response.json();
            this.displayResults(result);
            this.hideSection('progressSection');
            this.showSection('resultsSection');

        } catch (error) {
            console.error('Erreur:', error);
            this.showNotification('Erreur lors du traitement des fichiers.', 'error');
        } finally {
            this.hideLoadingOverlay();
        }
    }

    displayResults(results) {
        const resultsList = document.getElementById('resultsList');
        resultsList.innerHTML = '';

        results.files.forEach(file => {
            const resultItem = this.createResultItem(file);
            resultsList.appendChild(resultItem);
        });
    }

    createResultItem(file) {
        const resultItem = document.createElement('div');
        resultItem.className = 'result-item fade-in';
        
        resultItem.innerHTML = `
            <div class="result-info">
                <div class="result-icon">
                    <i class="fas fa-check"></i>
                </div>
                <div class="result-details">
                    <h4>${file.name}</h4>
                    <p>Traitement terminé avec succès</p>
                </div>
            </div>
            <div class="file-actions">
                <a href="${file.downloadUrl}" class="btn btn-primary btn-small" download>
                    <i class="fas fa-download"></i> Télécharger
                </a>
            </div>
        `;

        return resultItem;
    }

    clearFiles() {
        this.selectedFiles = [];
        this.selectedTool = null;
        
        // Remove active class from tool cards
        document.querySelectorAll('.tool-card').forEach(card => {
            card.classList.remove('active');
        });

        // Hide sections
        this.hideSection('filesSection');
        this.hideSection('progressSection');
        this.hideSection('resultsSection');

        // Reset file input
        document.getElementById('fileInput').value = '';

        this.showNotification('Fichiers effacés', 'success');
    }

    showSection(sectionId) {
        const section = document.getElementById(sectionId);
        section.style.display = 'block';
        section.classList.add('fade-in');
    }

    hideSection(sectionId) {
        const section = document.getElementById(sectionId);
        section.style.display = 'none';
        section.classList.remove('fade-in');
    }

    showLoadingOverlay() {
        document.getElementById('loadingOverlay').style.display = 'flex';
    }

    hideLoadingOverlay() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    showNotification(message, type = 'info') {
        // Créer l'élément de notification
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const icon = this.getNotificationIcon(type);
        notification.innerHTML = `
            <div class="notification-content">
                <i class="${icon}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

        // Ajouter au DOM
        document.body.appendChild(notification);

        // Animation d'entrée
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // Suppression automatique après 5 secondes
        setTimeout(() => {
            if (notification.parentElement) {
                notification.classList.remove('show');
                setTimeout(() => {
                    notification.remove();
                }, 300);
            }
        }, 5000);
    }

    getNotificationIcon(type) {
        const icons = {
            'success': 'fas fa-check-circle',
            'error': 'fas fa-exclamation-circle',
            'warning': 'fas fa-exclamation-triangle',
            'info': 'fas fa-info-circle'
        };
        return icons[type] || icons.info;
    }

    updateProgress(percentage, text) {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        if (progressFill) {
            progressFill.style.width = `${percentage}%`;
        }
        
        if (progressText && text) {
            progressText.textContent = text;
        }
    }

    // Méthode pour simuler le progrès (à remplacer par la vraie logique)
    simulateProgress() {
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
                this.updateProgress(progress, 'Traitement terminé !');
            } else {
                this.updateProgress(progress, `Traitement en cours... ${Math.round(progress)}%`);
            }
        }, 500);
    }
}

// Initialiser l'application
const app = new PDFApp();

// Styles pour les notifications
const notificationStyles = `
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        padding: 1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        min-width: 300px;
        max-width: 500px;
        transform: translateX(100%);
        opacity: 0;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        z-index: 1001;
        border-left: 4px solid;
    }

    .notification.show {
        transform: translateX(0);
        opacity: 1;
    }

    .notification-success {
        border-left-color: var(--success-color);
    }

    .notification-error {
        border-left-color: var(--danger-color);
    }

    .notification-warning {
        border-left-color: var(--warning-color);
    }

    .notification-info {
        border-left-color: var(--primary-color);
    }

    .notification-content {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .notification-content i {
        font-size: 1.2rem;
    }

    .notification-success .notification-content i {
        color: var(--success-color);
    }

    .notification-error .notification-content i {
        color: var(--danger-color);
    }

    .notification-warning .notification-content i {
        color: var(--warning-color);
    }

    .notification-info .notification-content i {
        color: var(--primary-color);
    }

    .notification-close {
        background: none;
        border: none;
        color: var(--text-secondary);
        cursor: pointer;
        padding: 0.25rem;
        border-radius: 4px;
        transition: var(--transition);
    }

    .notification-close:hover {
        background: var(--border-color);
        color: var(--text-primary);
    }
`;

// Ajouter les styles des notifications
const styleSheet = document.createElement('style');
styleSheet.textContent = notificationStyles;
document.head.appendChild(styleSheet);
