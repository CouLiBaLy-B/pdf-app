const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs').promises;
const { PDFDocument } = require('pdf-lib');

const app = express();
const PORT = process.env.PORT || 3000;

// Configuration de multer pour l'upload de fichiers
const storage = multer.diskStorage({
    destination: async (req, file, cb) => {
        const uploadDir = 'uploads';
        try {
            await fs.access(uploadDir);
        } catch {
            await fs.mkdir(uploadDir, { recursive: true });
        }
        cb(null, uploadDir);
    },
    filename: (req, file, cb) => {
        const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
        cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
    }
});

const upload = multer({ 
    storage: storage,
    fileFilter: (req, file, cb) => {
        if (file.mimetype === 'application/pdf') {
            cb(null, true);
        } else {
            cb(new Error('Seuls les fichiers PDF sont acceptés'), false);
        }
    },
    limits: {
        fileSize: 50 * 1024 * 1024 // 50MB max
    }
});

// Middleware
app.use(express.static('public'));
app.use(express.json());

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.post('/api/process', upload.array('files'), async (req, res) => {
    try {
        const { tool } = req.body;
        const files = req.files;

        if (!files || files.length === 0) {
            return res.status(400).json({ error: 'Aucun fichier fourni' });
        }

        let result;
        switch (tool) {
            case 'merge':
                result = await mergePDFs(files);
                break;
            case 'split':
                result = await splitPDF(files[0]);
                break;
            case 'compress':
                result = await compressPDFs(files);
                break;
            case 'convert':
                result = await convertPDFs(files);
                break;
            default:
                return res.status(400).json({ error: 'Outil non reconnu' });
        }

        res.json({
            success: true,
            tool: tool,
            files: result
        });

    } catch (error) {
        console.error('Erreur lors du traitement:', error);
        res.status(500).json({ 
            error: 'Erreur lors du traitement des fichiers',
            details: error.message 
        });
    }
});

// Fonction pour fusionner les PDFs
async function mergePDFs(files) {
    const mergedPdf = await PDFDocument.create();
    
    for (const file of files) {
        const pdfBytes = await fs.readFile(file.path);
        const pdf = await PDFDocument.load(pdfBytes);
        const copiedPages = await mergedPdf.copyPages(pdf, pdf.getPageIndices());
        copiedPages.forEach((page) => mergedPdf.addPage(page));
    }

    const pdfBytes = await mergedPdf.save();
    const outputPath = `uploads/merged-${Date.now()}.pdf`;
    await fs.writeFile(outputPath, pdfBytes);

    // Nettoyer les fichiers temporaires
    await Promise.all(files.map(file => fs.unlink(file.path).catch(() => {})));

    return [{
        name: 'document-fusionné.pdf',
        downloadUrl: `/${outputPath}`,
        size: pdfBytes.length
    }];
}

// Fonction pour diviser un PDF
async function splitPDF(file) {
    const pdfBytes = await fs.readFile(file.path);
    const pdf = await PDFDocument.load(pdfBytes);
    const pageCount = pdf.getPageCount();
    
    const results = [];
    
    for (let i = 0; i < pageCount; i++) {
        const newPdf = await PDFDocument.create();
        const [copiedPage] = await newPdf.copyPages(pdf, [i]);
        newPdf.addPage(copiedPage);
        
        const newPdfBytes = await newPdf.save();
        const outputPath = `uploads/page-${i + 1}-${Date.now()}.pdf`;
        await fs.writeFile(outputPath, newPdfBytes);
        
        results.push({
            name: `page-${i + 1}.pdf`,
            downloadUrl: `/${outputPath}`,
            size: newPdfBytes.length
        });
    }

    // Nettoyer le fichier temporaire
    await fs.unlink(file.path).catch(() => {});

    return results;
}

// Fonction pour compresser les PDFs (simulation)
async function compressPDFs(files) {
    const results = [];
    
    for (const file of files) {
        const pdfBytes = await fs.readFile(file.path);
        const pdf = await PDFDocument.load(pdfBytes);
        
        // Simulation de compression (dans un vrai projet, utilisez une vraie bibliothèque de compression)
        const compressedBytes = await pdf.save({
            useObjectStreams: false,
            addDefaultPage: false
        });
        
        const outputPath = `uploads/compressed-${Date.now()}-${file.originalname}`;
        await fs.writeFile(outputPath, compressedBytes);
        
        results.push({
            name: `compressed-${file.originalname}`,
            downloadUrl: `/${outputPath}`,
            size: compressedBytes.length,
            originalSize: file.size,
            compressionRatio: Math.round((1 - compressedBytes.length / file.size) * 100)
        });
    }

    // Nettoyer les fichiers temporaires
    await Promise.all(files.map(file => fs.unlink(file.path).catch(() => {})));

    return results;
}

// Fonction pour convertir les PDFs (simulation)
async function convertPDFs(files) {
    const results = [];
    
    for (const file of files) {
        // Simulation de conversion (dans un vrai projet, utilisez pdf2pic ou similar)
        const outputPath = `uploads/converted-${Date.now()}-${file.originalname.replace('.pdf', '.jpg')}`;
        
        // Pour la démo, on copie juste le fichier
        await fs.copyFile(file.path, outputPath);
        
        results.push({
            name: `converted-${file.originalname.replace('.pdf', '.jpg')}`,
            downloadUrl: `/${outputPath}`,
            size: file.size
        });
    }

    // Nettoyer les fichiers temporaires
    await Promise.all(files.map(file => fs.unlink(file.path).catch(() => {})));

    return results;
}

// Route pour télécharger les fichiers
app.get('/uploads/:filename', (req, res) => {
    const filename = req.params.filename;
    const filepath = path.join(__dirname, 'uploads', filename);
    res.download(filepath);
});

// Gestion des erreurs
app.use((error, req, res, next) => {
    if (error instanceof multer.MulterError) {
        if (error.code === 'LIMIT_FILE_SIZE') {
            return res.status(400).json({ error: 'Fichier trop volumineux (max 50MB)' });
        }
    }
    res.status(500).json({ error: error.message });
});

// Démarrage du serveur
app.listen(PORT, () => {
    console.log(`🚀 Serveur démarré sur http://localhost:${PORT}`);
    console.log(`📁 Interface disponible à l'adresse ci-dessus`);
});

// Nettoyage périodique des fichiers temporaires
setInterval(async () => {
    try {
        const uploadsDir = 'uploads';
        const files = await fs.readdir(uploadsDir);
        const now = Date.now();
        const maxAge = 24 * 60 * 60 * 1000; // 24 heures

        for (const file of files) {
            const filePath = path.join(uploadsDir, file);
            const stats = await fs.stat(filePath);
            
            if (now - stats.mtime.getTime() > maxAge) {
                await fs.unlink(filePath);
                console.log(`🗑️  Fichier supprimé: ${file}`);
            }
        }
    } catch (error) {
        console.error('Erreur lors du nettoyage:', error);
    }
}, 60 * 60 * 1000); // Vérification toutes les heures