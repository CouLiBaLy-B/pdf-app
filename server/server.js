const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const PDFDocument = require('pdfkit');
const { PDFDocument: PDFLib } = require('pdf-lib');

const app = express();
const PORT = process.env.PORT || 3000;

// Configuration multer pour l'upload de fichiers
const storage = multer.memoryStorage();
const upload = multer({ 
    storage: storage,
    limits: {
        fileSize: 50 * 1024 * 1024 // 50MB max
    },
    fileFilter: (req, file, cb) => {
        if (file.mimetype === 'application/pdf') {
            cb(null, true);
        } else {
            cb(new Error('Seuls les fichiers PDF sont acceptés'), false);
        }
    }
});

// Middleware
app.use(express.json({ limit: '50mb' }));
app.use(express.static('public'));
app.use('/uploads', express.static('uploads'));

// Créer le dossier uploads s'il n'existe pas
if (!fs.existsSync('uploads')) {
    fs.mkdirSync('uploads');
}

// Routes API

// Extraction de pages
app.post('/api/extract-pages', upload.single('pdf'), async (req, res) => {
    try {
        const { pages } = req.body;
        const pdfBuffer = req.file.buffer;
        
        const pdfDoc = await PDFLib.load(pdfBuffer);
        const newPdf = await PDFLib.create();
        
        for (const pageNum of pages) {
            const [copiedPage] = await newPdf.copyPages(pdfDoc, [pageNum - 1]);
            newPdf.addPage(copiedPage);
        }
        
        const pdfBytes = await newPdf.save();
        
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', 'attachment; filename="pages_extraites.pdf"');
        res.send(Buffer.from(pdfBytes));
        
    } catch (error) {
        console.error('Erreur extraction:', error);
        res.status(500).json({ error: 'Erreur lors de l\'extraction des pages' });
    }
});

// Fusion de PDFs
app.post('/api/merge-pdfs', upload.array('pdfs'), async (req, res) => {
    try {
        const mergedPdf = await PDFLib.create();
        
        for (const file of req.files) {
            const pdfDoc = await PDFLib.load(file.buffer);
            const pageCount = pdfDoc.getPageCount();
            
            for (let i = 0; i < pageCount; i++) {
                const [copiedPage] = await mergedPdf.copyPages(pdfDoc, [i]);
                mergedPdf.addPage(copiedPage);
            }
        }
        
        const pdfBytes = await mergedPdf.save();
        
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', 'attachment; filename="pdf_fusionne.pdf"');
        res.send(Buffer.from(pdfBytes));
        
    } catch (error) {
        console.error('Erreur fusion:', error);
        res.status(500).json({ error: 'Erreur lors de la fusion des PDFs' });
    }
});

// Rotation de pages
app.post('/api/rotate-pages', upload.single('pdf'), async (req, res) => {
    try {
        const { pages, angle } = req.body;
        const pdfBuffer = req.file.buffer;
        
        const pdfDoc = await PDFLib.load(pdfBuffer);
        const pageCount = pdfDoc.getPageCount();
        
        for (let i = 0; i < pageCount; i++) {
            if (pages.includes(i + 1)) {
                const page = pdfDoc.getPage(i);
                page.setRotation({ angle: parseInt(angle) });
            }
        }
        
        const pdfBytes = await pdfDoc.save();
        
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', 'attachment; filename="pdf_tourne.pdf"');
        res.send(Buffer.from(pdfBytes));
        
    } catch (error) {
        console.error('Erreur rotation:', error);
        res.status(500).json({ error: 'Erreur lors de la rotation des pages' });
    }
});

// Compression de PDF
app.post('/api/compress-pdf', upload.single('pdf'), async (req, res) => {
    try {
        const { level } = req.body;
        const pdfBuffer = req.file.buffer;
        
        // Charger le PDF
        const pdfDoc = await PDFLib.load(pdfBuffer);
        
        // Sauvegarder avec compression
        const pdfBytes = await pdfDoc.save({
            useObjectStreams: level === 'high',
            addDefaultPage: false,
            objectsPerTick: level === 'high' ? 50 : 200
        });
        
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', 'attachment; filename="pdf_compresse.pdf"');
        res.send(Buffer.from(pdfBytes));
        
    } catch (error) {
        console.error('Erreur compression:', error);
        res.status(500).json({ error: 'Erreur lors de la compression du PDF' });
    }
});

// Modification de métadonnées
app.post('/api/update-metadata', upload.single('pdf'), async (req, res) => {
    try {
        const { metadata } = req.body;
        const pdfBuffer = req.file.buffer;
        
        const pdfDoc = await PDFLib.load(pdfBuffer);
        
        // Mettre à jour les métadonnées
        if (metadata.title) pdfDoc.setTitle(metadata.title);
        if (metadata.author) pdfDoc.setAuthor(metadata.author);
        if (metadata.subject) pdfDoc.setSubject(metadata.subject);
        if (metadata.keywords) pdfDoc.setKeywords([metadata.keywords]);
        if (metadata.creator) pdfDoc.setCreator(metadata.creator);
        if (metadata.producer) pdfDoc.setProducer(metadata.producer);
        
        if (metadata.creationDate) {
            pdfDoc.setCreationDate(new Date(metadata.creationDate));
        }
        
        if (metadata.modificationDate) {
            pdfDoc.setModificationDate(new Date(metadata.modificationDate));
        }
        
        const pdfBytes = await pdfDoc.save();
        
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', 'attachment; filename="pdf_modifie.pdf"');
        res.send(Buffer.from(pdfBytes));
        
    } catch (error) {
        console.error('Erreur métadonnées:', error);
        res.status(500).json({ error: 'Erreur lors de la mise à jour des métadonnées' });
    }
});

// Sauvegarde avec modifications
app.post('/api/save-pdf', upload.single('pdf'), async (req, res) => {
    try {
        const { modifications } = req.body;
        const pdfBuffer = req.file.buffer;
        
        const pdfDoc = await PDFLib.load(pdfBuffer);
        
        // Appliquer les modifications
        for (const mod of modifications) {
            switch (mod.type) {
                case 'text':
                    await addTextToPDF(pdfDoc, mod.data);
                    break;
                case 'highlight':
                    await addHighlightToPDF(pdfDoc, mod.data);
                    break;
                case 'delete':
                    await deleteTextFromPDF(pdfDoc, mod.data);
                    break;
                case 'replace':
                    await replaceTextInPDF(pdfDoc, mod.data);
                    break;
                case 'note':
                    await addNoteToPDF(pdfDoc, mod.data);
                    break;
                case 'metadata':
                    await updatePDFMetadata(pdfDoc, mod.data);
                    break;
            }
        }
        
        const pdfBytes = await pdfDoc.save();
        
        res.setHeader('Content-Type', 'application/pdf');
        res.setHeader('Content-Disposition', 'attachment; filename="pdf_edite.pdf"');
        res.send(Buffer.from(pdfBytes));
        
    } catch (error) {
        console.error('Erreur sauvegarde:', error);
        res.status(500).json({ error: 'Erreur lors de la sauvegarde du PDF' });
    }
});

// Fonctions utilitaires pour les modifications PDF

async function addTextToPDF(pdfDoc, textData) {
    const page = pdfDoc.getPage(textData.page - 1);
    const { width, height } = page.getSize();
    
    page.drawText(textData.text, {
        x: textData.x,
        y: height - textData.y, // Inverser Y pour PDF
        size: textData.fontSize,
        color: hexToRgb(textData.color)
    });
}

async function addHighlightToPDF(pdfDoc, highlightData) {
    const page = pdfDoc.getPage(highlightData.page - 1);
    const { height } = page.getSize();
    
    page.drawRectangle({
        x: highlightData.x,
        y: height - highlightData.y - highlightData.height,
        width: highlightData.width,
        height: highlightData.height,
        color: hexToRgb(highlightData.color),
        opacity: 0.3
    });
}

async function deleteTextFromPDF(pdfDoc, deleteData) {
    const page = pdfDoc.getPage(deleteData.page - 1);
    const { height } = page.getSize();
    
    // Dessiner un rectangle blanc pour masquer le texte
    page.drawRectangle({
        x: deleteData.bounds.x1,
        y: height - deleteData.bounds.y2,
        width: deleteData.bounds.x2 - deleteData.bounds.x1,
        height: deleteData.bounds.y2 - deleteData.bounds.y1,
        color: { r: 1, g: 1, b: 1 }
    });
}

async function replaceTextInPDF(pdfDoc, replaceData) {
    // D'abord supprimer l'ancien texte
    await deleteTextFromPDF(pdfDoc, replaceData.original);
    
    // Puis ajouter le nouveau texte
    await addTextToPDF(pdfDoc, replaceData.replacement);
}

async function addNoteToPDF(pdfDoc, noteData) {
    const page = pdfDoc.getPage(noteData.page - 1);
    const { height } = page.getSize();
    
    // Ajouter un petit carré jaune pour la note
    page.drawRectangle({
        x: noteData.x - 10,
        y: height - noteData.y - 10,
        width: 20,
        height: 20,
        color: { r: 1, g: 1, b: 0 }
    });
    
    // Ajouter le texte "N"
    page.drawText('N', {
        x: noteData.x - 4,
        y: height - noteData.y + 4,
        size: 12,
        color: { r: 0, g: 0, b: 0 }
    });
}

async function updatePDFMetadata(pdfDoc, metadata) {
    if (metadata.title) pdfDoc.setTitle(metadata.title);
    if (metadata.author) pdfDoc.setAuthor(metadata.author);
    if (metadata.subject) pdfDoc.setSubject(metadata.subject);
    if (metadata.keywords) pdfDoc.setKeywords([metadata.keywords]);
    if (metadata.creator) pdfDoc.setCreator(metadata.creator);
    if (metadata.producer) pdfDoc.setProducer(metadata.producer);
    
    if (metadata.creationDate) {
        pdfDoc.setCreationDate(new Date(metadata.creationDate));
    }
    
    if (metadata.modificationDate) {
        pdfDoc.setModificationDate(new Date(metadata.modificationDate));
    }
}

function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16) / 255,
        g: parseInt(result[2], 16) / 255,
        b: parseInt(result[3], 16) / 255
    } : { r: 0, g: 0, b: 0 };
}

// Gestion des erreurs
app.use((error, req, res, next) => {
    if (error instanceof multer.MulterError) {
        if (error.code === 'LIMIT_FILE_SIZE') {
            return res.status(400).json({ error: 'Fichier trop volumineux (max 50MB)' });
        }
    }
    
    console.error('Erreur serveur:', error);
    res.status(500).json({ error: 'Erreur interne du serveur' });
});

// Route par défaut
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/index.html'));
});

// Démarrage du serveur
app.listen(PORT, () => {
    console.log(`Serveur démarré sur le port ${PORT}`);
    console.log(`Interface disponible sur http://localhost:${PORT}`);
});

module.exports = app;