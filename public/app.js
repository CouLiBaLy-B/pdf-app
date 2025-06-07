// Configuration PDF.js
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

class PDFEditorApp {
    constructor() {
        this.currentPDF = null;
        this.currentPage = 1;
        this.totalPages = 0;
        this.zoomLevel = 1.0;
        this.currentMode = 'select';
        this.selectedText = null;
        this.canvas = null;
        this.ctx = null;
        this.isSelecting = false;
        this.selectionStart = null;
        this.selectionEnd = null;
        this.textAnnotations = [];
        this.highlights = [];
        this.recentFiles = JSON.parse(localStorage.getItem('recentFiles') || '[]');
        this.modifications = [];
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupCanvas();
        this.loadRecentFiles();
        this.updateUI();
    }

    setupEventListeners() {
        // Navigation des onglets
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Upload de fichier
        const fileInput = document.getElementById('fileInput');
        const uploadArea = document.getElementById('uploadArea');

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.loadPDF(e.target.files[0]);
            }
        });

        // Drag & Drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0 && files[0].type === 'application/pdf') {
                this.loadPDF(files[0]);
            } else {
                this.showNotification('Veuillez sélectionner un fichier PDF valide', 'error');
            }
        });

        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        // Navigation des pages
        document.getElementById('firstPageBtn').addEventListener('click', () => this.goToPage(1));
        document.getElementById('prevPageBtn').addEventListener('click', () => this.goToPage(this.currentPage - 1));
        document.getElementById('nextPageBtn').addEventListener('click', () => this.goToPage(this.currentPage + 1));
        document.getElementById('lastPageBtn').addEventListener('click', () => this.goToPage(this.totalPages));
        
        document.getElementById('currentPageInput').addEventListener('change', (e) => {
            const page = parseInt(e.target.value);
            if (page >= 1 && page <= this.totalPages) {
                this.goToPage(page);
            }
        });

        // Contrôles de zoom
        document.getElementById('zoomInBtn').addEventListener('click', () => this.zoom(0.1));
        document.getElementById('zoomOutBtn').addEventListener('click', () => this.zoom(-0.1));

        // Sélection de mode
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setMode(e.target.dataset.mode);
            });
        });

        // Onglets d'outils
        document.querySelectorAll('.tool-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.switchToolPanel(e.target.dataset.tool);
            });
        });

        // Outils de texte
        document.getElementById('addTextBtn').addEventListener('click', () => this.addText());

        // Outils de sélection
        document.getElementById('deleteTextBtn').addEventListener('click', () => this.deleteSelectedText());
        document.getElementById('copyTextBtn').addEventListener('click', () => this.copySelectedText());
        document.getElementById('replaceTextBtn').addEventListener('click', () => this.replaceSelectedText());

        // Outils d'annotation
        document.getElementById('highlightBtn').addEventListener('click', () => this.highlightSelection());
        document.getElementById('addNoteBtn').addEventListener('click', () => this.addNote());

        // Sélecteur de couleur de surlignage
        document.querySelectorAll('.color-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.color-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });

        // Extraction de texte
        document.getElementById('extractPageBtn').addEventListener('click', () => this.extractCurrentPageText());
        document.getElementById('extractAllBtn').addEventListener('click', () => this.extractAllText());
        document.getElementById('saveTextBtn').addEventListener('click', () => this.saveExtractedText());

        // Manipulation
        document.getElementById('extractPagesBtn').addEventListener('click', () => this.extractPages());
        document.getElementById('mergeBtn').addEventListener('click', () => this.mergePDFs());
        document.getElementById('rotateBtn').addEventListener('click', () => this.rotatePages());
        document.getElementById('compressBtn').addEventListener('click', () => this.compressPDF());

        // Fichiers de fusion
        document.getElementById('mergeFiles').addEventListener('change', (e) => {
            this.addMergeFiles(e.target.files);
        });

        // Métadonnées
        document.getElementById('loadMetadataBtn').addEventListener('click', () => this.loadMetadata());
        document.getElementById('saveMetadataBtn').addEventListener('click', () => this.saveMetadata());

        // Sauvegarde
        document.getElementById('saveBtn').addEventListener('click', () => this.savePDF());
    }

    setupCanvas() {
        this.canvas = document.getElementById('pdfCanvas');
        this.ctx = this.canvas.getContext('2d');
        
        // Événements de sélection sur le canvas
        this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
        this.canvas.addEventListener('mousemove', (e) => this.onMouseMove(e));
        this.canvas.addEventListener('mouseup', (e) => this.onMouseUp(e));
        this.canvas.addEventListener('click', (e) => this.onCanvasClick(e));
    }

    async loadPDF(file) {
        this.showLoading('Chargement du PDF...');
        
        try {
            const arrayBuffer = await file.arrayBuffer();
            this.currentPDF = await pdfjsLib.getDocument(arrayBuffer).promise;
            this.totalPages = this.currentPDF.numPages;
            this.currentPage = 1;
            
            // Ajouter aux fichiers récents
            this.addToRecentFiles(file.name, arrayBuffer);
            
            // Afficher la première page
            await this.renderPage();
            
            // Mettre à jour l'interface
            this.updateUI();
            this.switchTab('editor');
            
            // Charger les métadonnées
            await this.loadPDFMetadata();
            
            this.showNotification('PDF chargé avec succès', 'success');
            
        } catch (error) {
            console.error('Erreur lors du chargement du PDF:', error);
            this.showNotification('Erreur lors du chargement du PDF', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async renderPage() {
        if (!this.currentPDF) return;

        try {
            const page = await this.currentPDF.getPage(this.currentPage);
            const viewport = page.getViewport({ scale: this.zoomLevel });
            
            this.canvas.width = viewport.width;
            this.canvas.height = viewport.height;
            
            const renderContext = {
                canvasContext: this.ctx,
                viewport: viewport
            };
            
            await page.render(renderContext).promise;
            
            // Redessiner les annotations
            this.redrawAnnotations();
            
            this.updatePageInfo();
            
        } catch (error) {
            console.error('Erreur lors du rendu de la page:', error);
            this.showNotification('Erreur lors du rendu de la page', 'error');
        }
    }

    redrawAnnotations() {
        // Redessiner les surlignages
        this.highlights.forEach(highlight => {
            if (highlight.page === this.currentPage) {
                this.drawHighlight(highlight);
            }
        });

        // Redessiner les annotations de texte
        this.textAnnotations.forEach(annotation => {
            if (annotation.page === this.currentPage) {
                this.drawTextAnnotation(annotation);
            }
        });
    }

    drawHighlight(highlight) {
        this.ctx.save();
        this.ctx.globalAlpha = 0.3;
        this.ctx.fillStyle = highlight.color;
        this.ctx.fillRect(highlight.x, highlight.y, highlight.width, highlight.height);
        this.ctx.restore();
    }

    drawTextAnnotation(annotation) {
        this.ctx.save();
        this.ctx.font = `${annotation.fontSize}px Arial`;
        this.ctx.fillStyle = annotation.color;
        this.ctx.fillText(annotation.text, annotation.x, annotation.y);
        this.ctx.restore();
    }

    onMouseDown(e) {
        if (this.currentMode === 'select' || this.currentMode === 'highlight') {
            this.isSelecting = true;
            const rect = this.canvas.getBoundingClientRect();
            this.selectionStart = {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            };
        }
    }

    onMouseMove(e) {
        if (this.isSelecting && this.selectionStart) {
            const rect = this.canvas.getBoundingClientRect();
            this.selectionEnd = {
                x: e.clientX - rect.left,
                y: e.clientY - rect.top
            };
            this.drawSelectionRect();
        }
    }

    onMouseUp(e) {
        if (this.isSelecting) {
            this.isSelecting = false;
            
            if (this.selectionStart && this.selectionEnd) {
                if (this.currentMode === 'select') {
                    this.handleTextSelection();
                } else if (this.currentMode === 'highlight') {
                    this.createHighlight();
                }
            }
        }
    }

    onCanvasClick(e) {
        if (this.currentMode === 'text') {
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            document.getElementById('textX').value = Math.round(x);
            document.getElementById('textY').value = Math.round(y);
        }
    }

    drawSelectionRect() {
        if (!this.selectionStart || !this.selectionEnd) return;
        
        // Redessiner la page
        this.renderPage();
        
        // Dessiner le rectangle de sélection
        this.ctx.save();
        this.ctx.strokeStyle = '#2563eb';
        this.ctx.lineWidth = 2;
        this.ctx.setLineDash([5, 5]);
        
        const x = Math.min(this.selectionStart.x, this.selectionEnd.x);
        const y = Math.min(this.selectionStart.y, this.selectionEnd.y);
        const width = Math.abs(this.selectionEnd.x - this.selectionStart.x);
        const height = Math.abs(this.selectionEnd.y - this.selectionStart.y);
        
        this.ctx.strokeRect(x, y, width, height);
        this.ctx.restore();
    }

    async handleTextSelection() {
        if (!this.currentPDF || !this.selectionStart || !this.selectionEnd) return;

        try {
            const page = await this.currentPDF.getPage(this.currentPage);
            const viewport = page.getViewport({ scale: this.zoomLevel });
            
            // Convertir les coordonnées canvas en coordonnées PDF
            const x1 = Math.min(this.selectionStart.x, this.selectionEnd.x) / this.zoomLevel;
            const y1 = (viewport.height - Math.max(this.selectionStart.y, this.selectionEnd.y)) / this.zoomLevel;
            const x2 = Math.max(this.selectionStart.x, this.selectionEnd.x) / this.zoomLevel;
            const y2 = (viewport.height - Math.min(this.selectionStart.y, this.selectionEnd.y)) / this.zoomLevel;
            
            // Extraire le texte dans la zone sélectionnée
            const textContent = await page.getTextContent();
            let selectedText = '';
            
            textContent.items.forEach(item => {
                const transform = item.transform;
                const x = transform[4];
                const y = transform[5];
                
                if (x >= x1 && x <= x2 && y >= y1 && y <= y2) {
                    selectedText += item.str + ' ';
                }
            });
            
            if (selectedText.trim()) {
                this.selectedText = {
                    text: selectedText.trim(),
                    page: this.currentPage,
                    bounds: { x1, y1, x2, y2 }
                };
                
                this.updateSelectionInfo();
                this.switchToolPanel('selection');
            }
            
        } catch (error) {
            console.error('Erreur lors de la sélection de texte:', error);
        }
    }

    createHighlight() {
        if (!this.selectionStart || !this.selectionEnd) return;
        
        const activeColorBtn = document.querySelector('.color-btn.active');
        const color = activeColorBtn ? activeColorBtn.dataset.color : 'yellow';
        
        const x = Math.min(this.selectionStart.x, this.selectionEnd.x);
        const y = Math.min(this.selectionStart.y, this.selectionEnd.y);
        const width = Math.abs(this.selectionEnd.x - this.selectionStart.x);
        const height = Math.abs(this.selectionEnd.y - this.selectionStart.y);
        
        const highlight = {
            page: this.currentPage,
            x, y, width, height,
            color: this.getColorValue(color)
        };
        
        this.highlights.push(highlight);
        this.modifications.push({
            type: 'highlight',
            data: highlight
        });
        
        this.drawHighlight(highlight);
        this.updateSaveButton();
        
        this.selectionStart = null;
        this.selectionEnd = null;
    }

    getColorValue(colorName) {
        const colors = {
            yellow: '#ffff00',
            green: '#90ee90',
            blue: '#add8e6',
            pink: '#ffb6c1'
        };
        return colors[colorName] || '#ffff00';
    }

    updateSelectionInfo() {
        const selectionInfo = document.getElementById('selectionInfo');
        const deleteBtn = document.getElementById('deleteTextBtn');
        const copyBtn = document.getElementById('copyTextBtn');
        const replaceBtn = document.getElementById('replaceTextBtn');
        const highlightBtn = document.getElementById('highlightBtn');
        
        if (this.selectedText) {
            selectionInfo.innerHTML = `
                <p><strong>Texte sélectionné:</strong></p>
                <p>"${this.selectedText.text.substring(0, 100)}${this.selectedText.text.length > 100 ? '...' : ''}"</p>
                <p><strong>Page:</strong> ${this.selectedText.page}</p>
                <p><strong>Position:</strong> (${Math.round(this.selectedText.bounds.x1)}, ${Math.round(this.selectedText.bounds.y1)})</p>
            `;
            
            deleteBtn.disabled = false;
            copyBtn.disabled = false;
            replaceBtn.disabled = false;
            highlightBtn.disabled = false;
            
            // Pré-remplir le texte de remplacement
            document.getElementById('replacementText').value = this.selectedText.text;
            
        } else {
            selectionInfo.innerHTML = '<p>Aucune sélection</p>';
            deleteBtn.disabled = true;
            copyBtn.disabled = true;
            replaceBtn.disabled = true;
            highlightBtn.disabled = true;
        }
    }

    addText() {
        const text = document.getElementById('newTextInput').value.trim();
        const x = parseInt(document.getElementById('textX').value);
        const y = parseInt(document.getElementById('textY').value);
        const fontSize = parseInt(document.getElementById('fontSize').value);
        const color = document.getElementById('textColor').value;
        
        if (!text) {
            this.showNotification('Veuillez entrer du texte', 'warning');
            return;
        }
        
        const annotation = {
            type: 'text',
            page: this.currentPage,
            text,
            x,
            y,
            fontSize,
            color: this.getTextColor(color)
        };
        
        this.textAnnotations.push(annotation);
        this.modifications.push({
            type: 'text',
            data: annotation
        });
        
        this.drawTextAnnotation(annotation);
        this.updateSaveButton();
        
        // Réinitialiser le formulaire
        document.getElementById('newTextInput').value = '';
        
        this.showNotification('Texte ajouté avec succès', 'success');
    }

    getTextColor(colorName) {
        const colors = {
            black: '#000000',
            red: '#ff0000',
            blue: '#0000ff',
            green: '#008000'
        };
        return colors[colorName] || '#000000';
    }

    deleteSelectedText() {
        if (!this.selectedText) return;
        
        // Ajouter une modification de suppression
        this.modifications.push({
            type: 'delete',
            data: this.selectedText
        });
        
        // Créer un rectangle blanc pour masquer le texte
        const highlight = {
            page: this.selectedText.page,
            x: this.selectedText.bounds.x1 * this.zoomLevel,
            y: (this.canvas.height - this.selectedText.bounds.y2 * this.zoomLevel),
            width: (this.selectedText.bounds.x2 - this.selectedText.bounds.x1) * this.zoomLevel,
            height: (this.selectedText.bounds.y2 - this.selectedText.bounds.y1) * this.zoomLevel,
            color: '#ffffff'
        };
        
        this.highlights.push(highlight);
        this.drawHighlight(highlight);
        
        this.selectedText = null;
        this.updateSelectionInfo();
        this.updateSaveButton();
        
        this.showNotification('Texte supprimé', 'success');
    }

    copySelectedText() {
        if (!this.selectedText) return;
        
        navigator.clipboard.writeText(this.selectedText.text).then(() => {
            this.showNotification('Texte copié dans le presse-papiers', 'success');
        }).catch(() => {
            this.showNotification('Erreur lors de la copie', 'error');
        });
    }

    replaceSelectedText() {
        if (!this.selectedText) return;
        
        const newText = document.getElementById('replacementText').value.trim();
        if (!newText) {
            this.showNotification('Veuillez entrer le texte de remplacement', 'warning');
            return;
        }
        
        // Supprimer l'ancien texte
        this.deleteSelectedText();
        
        // Ajouter le nouveau texte
        const annotation = {
            type: 'text',
            page: this.currentPage,
            text: newText,
            x: this.selectedText.bounds.x1 * this.zoomLevel,
            y: this.canvas.height - this.selectedText.bounds.y1 * this.zoomLevel,
            fontSize: 12,
            color: '#000000'
        };
        
        this.textAnnotations.push(annotation);
        this.modifications.push({
            type: 'replace',
            data: { original: this.selectedText, replacement: annotation }
        });
        
        this.drawTextAnnotation(annotation);
        
        this.selectedText = null;
        this.updateSelectionInfo();
        this.updateSaveButton();
        
        this.showNotification('Texte remplacé avec succès', 'success');
    }

    highlightSelection() {
        if (!this.selectedText) return;
        
        const activeColorBtn = document.querySelector('.color-btn.active');
        const color = activeColorBtn ? activeColorBtn.dataset.color : 'yellow';
        
        const highlight = {
            page: this.selectedText.page,
            x: this.selectedText.bounds.x1 * this.zoomLevel,
            y: this.canvas.height - this.selectedText.bounds.y2 * this.zoomLevel,
            width: (this.selectedText.bounds.x2 - this.selectedText.bounds.x1) * this.zoomLevel,
            height: (this.selectedText.bounds.y2 - this.selectedText.bounds.y1) * this.zoomLevel,
            color: this.getColorValue(color)
        };
        
        this.highlights.push(highlight);
        this.modifications.push({
            type: 'highlight',
            data: highlight
        });
        
        this.drawHighlight(highlight);
        this.updateSaveButton();
        
        this.showNotification('Surlignage appliqué', 'success');
    }

    addNote() {
        const content = document.getElementById('noteContent').value.trim();
        if (!content) {
            this.showNotification('Veuillez entrer le contenu de la note', 'warning');
            return;
        }
        
        // Ajouter une note au centre de la page
        const x = this.canvas.width / 2;
        const y = this.canvas.height / 2;
        
        const note = {
            type: 'note',
            page: this.currentPage,
            content,
            x,
            y
        };
        
        this.modifications.push({
            type: 'note',
            data: note
        });
        
        // Dessiner un indicateur de note
        this.ctx.save();
        this.ctx.fillStyle = '#fbbf24';
        this.ctx.fillRect(x - 10, y - 10, 20, 20);
        this.ctx.fillStyle = '#000000';
        this.ctx.font = '12px Arial';
        this.ctx.fillText('N', x - 4, y + 4);
        this.ctx.restore();
        
        document.getElementById('noteContent').value = '';
        this.updateSaveButton();
        
        this.showNotification('Note ajoutée', 'success');
    }

    async extractCurrentPageText() {
        if (!this.currentPDF) return;
        
        try {
            const page = await this.currentPDF.getPage(this.currentPage);
            const textContent = await page.getTextContent();
            
            let text = '';
            textContent.items.forEach(item => {
                text += item.str + ' ';
            });
            
            document.getElementById('extractedText').value = text.trim();
            document.getElementById('saveTextBtn').disabled = false;
            
            this.showNotification('Texte de la page extrait', 'success');
            
        } catch (error) {
            console.error('Erreur lors de l\'extraction:', error);
            this.showNotification('Erreur lors de l\'extraction du texte', 'error');
        }
    }

    async extractAllText() {
        if (!this.currentPDF) return;
        
        this.showLoading('Extraction du texte...');
        
        try {
            let allText = '';
            
            for (let i = 1; i <= this.totalPages; i++) {
                const page = await this.currentPDF.getPage(i);
                const textContent = await page.getTextContent();
                
                allText += `--- Page ${i} ---\n`;
                textContent.items.forEach(item => {
                    allText += item.str + ' ';
                });
                allText += '\n\n';
            }
            
            document.getElementById('extractedText').value = allText.trim();
            document.getElementById('saveTextBtn').disabled = false;
            
            this.showNotification('Texte complet extrait', 'success');
            
        } catch (error) {
            console.error('Erreur lors de l\'extraction:', error);
            this.showNotification('Erreur lors de l\'extraction du texte', 'error');
        } finally {
            this.hideLoading();
        }
    }

    saveExtractedText() {
        const text = document.getElementById('extractedText').value;
        if (!text) return;
        
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'texte_extrait.txt';
        a.click();
        URL.revokeObjectURL(url);
        
        this.showNotification('Texte sauvegardé', 'success');
    }

    async extractPages() {
        const pagesInput = document.getElementById('extractPages').value.trim();
        if (!pagesInput) {
            this.showNotification('Veuillez spécifier les pages à extraire', 'warning');
            return;
        }
        
        try {
            const pages = this.parsePageRange(pagesInput);
            if (pages.some(p => p < 1 || p > this.totalPages)) {
                this.showNotification('Numéros de pages invalides', 'error');
                return;
            }
            
            this.showLoading('Extraction des pages...');
            
            // Envoyer la demande au serveur
            const response = await fetch('/api/extract-pages', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    pages: pages,
                    // Ici on devrait envoyer le PDF, mais pour la démo on simule
                })
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'pages_extraites.pdf';
                a.click();
                URL.revokeObjectURL(url);
                
                this.showNotification('Pages extraites avec succès', 'success');
            } else {
                throw new Error('Erreur serveur');
            }
            
        } catch (error) {
            console.error('Erreur lors de l\'extraction:', error);
            this.showNotification('Erreur lors de l\'extraction des pages', 'error');
        } finally {
            this.hideLoading();
        }
    }

    addMergeFiles(files) {
        const mergeList = document.getElementById('mergeList');
        const mergeBtn = document.getElementById('mergeBtn');
        
        Array.from(files).forEach(file => {
            if (file.type === 'application/pdf') {
                const item = document.createElement('div');
                item.className = 'merge-item';
                item.innerHTML = `
                    <span><i class="fas fa-file-pdf"></i> ${file.name}</span>
                    <button class="btn btn-small btn-danger" onclick="this.parentElement.remove(); this.updateMergeButton();">
                        <i class="fas fa-times"></i>
                    </button>
                `;
                mergeList.appendChild(item);
            }
        });
        
        mergeBtn.disabled = mergeList.children.length < 2;
    }

    async mergePDFs() {
        const mergeList = document.getElementById('mergeList');
        if (mergeList.children.length < 2) {
            this.showNotification('Sélectionnez au moins 2 fichiers PDF', 'warning');
            return;
        }
        
        this.showLoading('Fusion des PDF...');
        
        try {
            // Simulation de la fusion (dans une vraie app, on enverrait les fichiers au serveur)
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            this.showNotification('PDF fusionnés avec succès', 'success');
            
        } catch (error) {
            console.error('Erreur lors de la fusion:', error);
            this.showNotification('Erreur lors de la fusion', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async rotatePages() {
        const pagesInput = document.getElementById('rotatePages').value.trim();
        const angle = document.getElementById('rotateAngle').value;
        
        if (!pagesInput) {
            this.showNotification('Veuillez spécifier les pages à faire tourner', 'warning');
            return;
        }
        
        try {
            const pages = this.parsePageRange(pagesInput);
            if (pages.some(p => p < 1 || p > this.totalPages)) {
                this.showNotification('Numéros de pages invalides', 'error');
                return;
            }
            
            this.showLoading('Rotation des pages...');
            
            // Simulation de la rotation
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            this.showNotification(`Pages tournées de ${angle}°`, 'success');
            
        } catch (error) {
            console.error('Erreur lors de la rotation:', error);
            this.showNotification('Erreur lors de la rotation', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async compressPDF() {
        if (!this.currentPDF) {
            this.showNotification('Aucun PDF chargé', 'warning');
            return;
        }
        
        const level = document.getElementById('compressionLevel').value;
        
        this.showLoading('Compression du PDF...');
        
        try {
            // Simulation de la compression
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            this.showNotification('PDF compressé avec succès', 'success');
            
        } catch (error) {
            console.error('Erreur lors de la compression:', error);
            this.showNotification('Erreur lors de la compression', 'error');
        } finally {
            this.hideLoading();
        }
    }

    async loadPDFMetadata() {
        if (!this.currentPDF) return;
        
        try {
            const metadata = await this.currentPDF.getMetadata();
            
            // Remplir les champs de métadonnées
            document.getElementById('metaTitle').value = metadata.info.Title || '';
            document.getElementById('metaAuthor').value = metadata.info.Author || '';
            document.getElementById('metaSubject').value = metadata.info.Subject || '';
            document.getElementById('metaKeywords').value = metadata.info.Keywords || '';
            document.getElementById('metaCreator').value = metadata.info.Creator || '';
            document.getElementById('metaProducer').value = metadata.info.Producer || '';
            
            // Dates
            if (metadata.info.CreationDate) {
                const creationDate = new Date(metadata.info.CreationDate);
                document.getElementById('metaCreationDate').value = this.formatDateForInput(creationDate);
            }
            
            if (metadata.info.ModDate) {
                const modDate = new Date(metadata.info.ModDate);
                document.getElementById('metaModificationDate').value = this.formatDateForInput(modDate);
            }
            
            // Mettre à jour les statistiques
            this.updateDocumentStats();
            
        } catch (error) {
            console.error('Erreur lors du chargement des métadonnées:', error);
        }
    }

    formatDateForInput(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    }

    async updateDocumentStats() {
        if (!this.currentPDF) return;
        
        try {
            // Nombre de pages
            document.getElementById('pageCount').textContent = this.totalPages;
            
            // Taille du fichier (estimation)
            document.getElementById('fileSize').textContent = 'N/A';
            
            // Compter les mots et caractères
            let totalWords = 0;
            let totalChars = 0;
            
            for (let i = 1; i <= Math.min(this.totalPages, 5); i++) { // Limiter pour la performance
                const page = await this.currentPDF.getPage(i);
                const textContent = await page.getTextContent();
                
                let pageText = '';
                textContent.items.forEach(item => {
                    pageText += item.str + ' ';
                });
                
                const words = pageText.trim().split(/\s+/).filter(word => word.length > 0);
                totalWords += words.length;
                totalChars += pageText.length;
            }
            
            // Extrapoler pour toutes les pages
            if (this.totalPages > 5) {
                totalWords = Math.round(totalWords * this.totalPages / 5);
                totalChars = Math.round(totalChars * this.totalPages / 5);
            }
            
            document.getElementById('wordCount').textContent = totalWords.toLocaleString();
            document.getElementById('charCount').textContent = totalChars.toLocaleString();
            
        } catch (error) {
            console.error('Erreur lors du calcul des statistiques:', error);
        }
    }

    loadMetadata() {
        this.loadPDFMetadata();
        this.showNotification('Métadonnées rechargées', 'info');
    }

    saveMetadata() {
        const metadata = {
            title: document.getElementById('metaTitle').value,
            author: document.getElementById('metaAuthor').value,
            subject: document.getElementById('metaSubject').value,
            keywords: document.getElementById('metaKeywords').value,
            creator: document.getElementById('metaCreator').value,
            producer: document.getElementById('metaProducer').value,
            creationDate: document.getElementById('metaCreationDate').value,
            modificationDate: document.getElementById('metaModificationDate').value
        };
        
        this.modifications.push({
            type: 'metadata',
            data: metadata
        });
        
        this.updateSaveButton();
        this.showNotification('Métadonnées mises à jour', 'success');
    }

    parsePageRange(input) {
        const pages = [];
        const parts = input.split(',');
        
        parts.forEach(part => {
            part = part.trim();
            if (part.includes('-')) {
                const [start, end] = part.split('-').map(n => parseInt(n.trim()));
                for (let i = start; i <= end; i++) {
                    pages.push(i);
                }
            } else {
                pages.push(parseInt(part));
            }
        });
        
        return [...new Set(pages)].sort((a, b) => a - b);
    }

    goToPage(pageNum) {
        if (pageNum >= 1 && pageNum <= this.totalPages && pageNum !== this.currentPage) {
            this.currentPage = pageNum;
            this.renderPage();
        }
    }

    zoom(delta) {
        const newZoom = Math.max(0.5, Math.min(3.0, this.zoomLevel + delta));
        if (newZoom !== this.zoomLevel) {
            this.zoomLevel = newZoom;
            this.renderPage();
            this.updateZoomDisplay();
        }
    }

    setMode(mode) {
        this.currentMode = mode;
        
        // Mettre à jour l'interface
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === mode);
        });
        
        // Changer le curseur du canvas
        const cursors = {
            select: 'crosshair',
            text: 'text',
            highlight: 'pointer'
        };
        
        this.canvas.style.cursor = cursors[mode] || 'default';
        
        // Réinitialiser la sélection
        this.selectedText = null;
        this.updateSelectionInfo();
    }

    switchTab(tabName) {
        // Masquer tous les contenus d'onglets
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Masquer tous les boutons de navigation
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Afficher l'onglet sélectionné
        document.getElementById(`${tabName}-tab`).classList.add('active');
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    }

    switchToolPanel(toolName) {
        // Masquer tous les panneaux d'outils
        document.querySelectorAll('.tool-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        
        // Masquer tous les onglets d'outils
        document.querySelectorAll('.tool-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Afficher le panneau sélectionné
        document.getElementById(`${toolName}-panel`).classList.add('active');
        document.querySelector(`[data-tool="${toolName}"]`).classList.add('active');
    }

    updateUI() {
        const hasDocument = this.currentPDF !== null;
        
        // Activer/désactiver les contrôles
        document.getElementById('firstPageBtn').disabled = !hasDocument || this.currentPage === 1;
        document.getElementById('prevPageBtn').disabled = !hasDocument || this.currentPage === 1;
        document.getElementById('nextPageBtn').disabled = !hasDocument || this.currentPage === this.totalPages;
        document.getElementById('lastPageBtn').disabled = !hasDocument || this.currentPage === this.totalPages;
        document.getElementById('currentPageInput').disabled = !hasDocument;
        document.getElementById('zoomInBtn').disabled = !hasDocument;
        document.getElementById('zoomOutBtn').disabled = !hasDocument;
        
        // Mettre à jour les informations
        this.updatePageInfo();
        this.updateZoomDisplay();
        this.updateStatusBar();
        this.updateSaveButton();
    }

    updatePageInfo() {
        document.getElementById('currentPageInput').value = this.currentPage;
        document.getElementById('totalPages').textContent = this.totalPages;
    }

    updateZoomDisplay() {
        document.getElementById('zoomLevel').textContent = `${Math.round(this.zoomLevel * 100)}%`;
    }

    updateStatusBar() {
        const statusText = document.getElementById('statusText');
        const documentInfo = document.getElementById('documentInfo');
        
        if (this.currentPDF) {
            statusText.textContent = 'Document chargé';
            documentInfo.textContent = `Page ${this.currentPage} sur ${this.totalPages}`;
        } else {
            statusText.textContent = 'Prêt';
            documentInfo.textContent = 'Aucun document chargé';
        }
    }

    updateSaveButton() {
        const saveBtn = document.getElementById('saveBtn');
        saveBtn.disabled = this.modifications.length === 0;
        
        if (this.modifications.length > 0) {
            saveBtn.innerHTML = `<i class="fas fa-save"></i> Sauvegarder (${this.modifications.length})`;
        } else {
            saveBtn.innerHTML = '<i class="fas fa-save"></i> Sauvegarder';
        }
    }

    async savePDF() {
        if (this.modifications.length === 0) {
            this.showNotification('Aucune modification à sauvegarder', 'info');
            return;
        }
        
        this.showLoading('Sauvegarde du PDF...');
        
        try {
            // Dans une vraie application, on enverrait les modifications au serveur
            // Ici on simule la sauvegarde
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Réinitialiser les modifications
            this.modifications = [];
            this.updateSaveButton();
            
            this.showNotification('PDF sauvegardé avec succès', 'success');
            
        } catch (error) {
            console.error('Erreur lors de la sauvegarde:', error);
            this.showNotification('Erreur lors de la sauvegarde', 'error');
        } finally {
            this.hideLoading();
        }
    }

    addToRecentFiles(fileName, arrayBuffer) {
        const fileData = {
            name: fileName,
            date: new Date().toISOString(),
            size: arrayBuffer.byteLength
        };
        
        // Supprimer le fichier s'il existe déjà
        this.recentFiles = this.recentFiles.filter(file => file.name !== fileName);
        
        // Ajouter en première position
        this.recentFiles.unshift(fileData);
        
        // Limiter à 10 fichiers récents
        this.recentFiles = this.recentFiles.slice(0, 10);
        
        // Sauvegarder dans localStorage
        localStorage.setItem('recentFiles', JSON.stringify(this.recentFiles));
        
        this.loadRecentFiles();
    }

    loadRecentFiles() {
        const recentList = document.getElementById('recentList');
        recentList.innerHTML = '';
        
        if (this.recentFiles.length === 0) {
            recentList.innerHTML = '<p class="text-center">Aucun fichier récent</p>';
            return;
        }
        
        this.recentFiles.forEach(file => {
            const item = document.createElement('div');
            item.className = 'recent-item';
            item.innerHTML = `
                <div>
                    <div style="font-weight: 500;">${file.name}</div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary);">
                        ${new Date(file.date).toLocaleDateString()} - ${this.formatFileSize(file.size)}
                    </div>
                </div>
                <button class="btn btn-small btn-primary">
                    <i class="fas fa-folder-open"></i>
                </button>
            `;
            
            item.addEventListener('click', () => {
                // Dans une vraie app, on rechargerait le fichier depuis le stockage
                this.showNotification('Fonctionnalité non implémentée dans la démo', 'info');
            });
            
            recentList.appendChild(item);
        });
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    showLoading(message = 'Chargement...') {
        const overlay = document.getElementById('loadingOverlay');
        const text = document.getElementById('loadingText');
        text.textContent = message;
        overlay.style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notificationContainer');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        notification.innerHTML = `
            <i class="notification-icon ${icons[type]}"></i>
            <div class="notification-content">${message}</div>
            <button class="notification-close">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Ajouter l'événement de fermeture
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.hideNotification(notification);
        });
        
        container.appendChild(notification);
        
        // Afficher avec animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        // Masquer automatiquement après 5 secondes
        setTimeout(() => {
            this.hideNotification(notification);
        }, 5000);
    }

    hideNotification(notification) {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }
}

// Initialiser l'application
document.addEventListener('DOMContentLoaded', () => {
    new PDFEditorApp();
});

// Gestion des raccourcis clavier
document.addEventListener('keydown', (e) => {
    // Ctrl+O - Ouvrir fichier
    if (e.ctrlKey && e.key === 'o') {
        e.preventDefault();
        document.getElementById('fileInput').click();
    }
    
    // Ctrl+S - Sauvegarder
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        const saveBtn = document.getElementById('saveBtn');
        if (!saveBtn.disabled) {
            saveBtn.click();
        }
    }
    
    // Flèches pour navigation
    if (e.key === 'ArrowLeft' && !e.target.matches('input, textarea')) {
        e.preventDefault();
        document.getElementById('prevPageBtn').click();
    }
    
    if (e.key === 'ArrowRight' && !e.target.matches('input, textarea')) {
        e.preventDefault();
        document.getElementById('nextPageBtn').click();
    }
    
    // + et - pour zoom
    if (e.key === '+' && e.ctrlKey) {
        e.preventDefault();
        document.getElementById('zoomInBtn').click();
    }
    
    if (e.key === '-' && e.ctrlKey) {
        e.preventDefault();
        document.getElementById('zoomOutBtn').click();
    }
    
    // Échap pour annuler sélection
    if (e.key === 'Escape') {
        // Réinitialiser la sélection si elle existe
        if (window.pdfApp && window.pdfApp.selectedText) {
            window.pdfApp.selectedText = null;
            window.pdfApp.updateSelectionInfo();
        }
    }
});

// Exposer l'instance de l'app globalement pour les raccourcis
window.addEventListener('load', () => {
    window.pdfApp = new PDFEditorApp();
});
