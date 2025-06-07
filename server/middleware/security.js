const rateLimit = require('express-rate-limit');
const helmet = require('helmet');
const { securityLogger } = require('./logger');

// Configuration du rate limiting
const createRateLimiter = (windowMs, max, message) => {
    return rateLimit({
        windowMs,
        max,
        message: { error: message },
        standardHeaders: true,
        legacyHeaders: false,
        handler: (req, res) => {
            securityLogger.rateLimitExceeded(req);
            res.status(429).json({ error: message });
        }
    });
};

// Rate limiters spécialisés
const rateLimiters = {
    // Limite générale
    general: createRateLimiter(
        15 * 60 * 1000, // 15 minutes
        100, // 100 requêtes
        'Trop de requêtes, veuillez réessayer plus tard'
    ),
    
    // Limite pour les uploads
    upload: createRateLimiter(
        60 * 1000, // 1 minute
        5, // 5 uploads
        'Trop d\'uploads, veuillez attendre avant de réessayer'
    ),
    
    // Limite stricte pour les opérations sensibles
    strict: createRateLimiter(
        60 * 1000, // 1 minute
        3, // 3 requêtes
        'Limite de sécurité atteinte'
    )
};

// Validation des fichiers uploadés
const fileValidation = {
    // Vérifier le type MIME
    validateMimeType: (file) => {
        const allowedTypes = [
            'application/pdf',
            'application/x-pdf',
            'application/acrobat',
            'applications/vnd.pdf',
            'text/pdf',
            'text/x-pdf'
        ];
        
        return allowedTypes.includes(file.mimetype.toLowerCase());
    },
    
    // Vérifier la signature du fichier (magic bytes)
    validateFileSignature: (buffer) => {
        // Signature PDF: %PDF-
        const pdfSignature = Buffer.from([0x25, 0x50, 0x44, 0x46, 0x2D]);
        return buffer.subarray(0, 5).equals(pdfSignature);
    },
    
    // Vérifier la taille du fichier
    validateFileSize: (size, maxSize = 50 * 1024 * 1024) => {
        return size <= maxSize;
    },
    
    // Validation complète
    validateFile: (file, buffer) => {
        const errors = [];
        
        if (!fileValidation.validateMimeType(file)) {
            errors.push('Type de fichier non autorisé');
        }
        
        if (!fileValidation.validateFileSignature(buffer)) {
            errors.push('Signature de fichier invalide');
        }
        
        if (!fileValidation.validateFileSize(file.size)) {
            errors.push('Fichier trop volumineux');
        }
        
        return {
            isValid: errors.length === 0,
            errors
        };
    }
};

// Middleware de validation des fichiers
const fileValidationMiddleware = (req, res, next) => {
    if (!req.file && !req.files) {
        return next();
    }
    
    const files = req.files || [req.file];
    
    for (const file of files) {
        if (file && file.buffer) {
            const validation = fileValidation.validateFile(file, file.buffer);
            
            if (!validation.isValid) {
                securityLogger.fileUploadRejected(
                    validation.errors.join(', '),
                    req,
                    {
                        originalname: file.originalname,
                        size: file.size,
                        mimetype: file.mimetype
                    }
                );
                
                return res.status(400).json({
                    error: 'Fichier invalide',
                    details: validation.errors
                });
            }
        }
    }
    
    next();
};

// Détection d'activités suspectes
const suspiciousActivityDetector = (req, res, next) => {
    const suspiciousPatterns = [
        // Tentatives d'injection
        /<script|javascript:|vbscript:|onload=|onerror=/i,
        // Tentatives de traversée de répertoire
        /\.\.[\/\\]/,
        // Tentatives SQL injection
        /union\s+select|drop\s+table|insert\s+into/i,
        // Tentatives XSS
        /<iframe|<object|<embed/i
    ];
    
    const checkString = `${req.url} ${JSON.stringify(req.query)} ${JSON.stringify(req.body)}`;
    
    for (const pattern of suspiciousPatterns) {
        if (pattern.test(checkString)) {
            securityLogger.suspiciousActivity(
                'Pattern matching detected',
                req,
                { pattern: pattern.toString() }
            );
            
            return res.status(400).json({
                error: 'Requête invalide'
            });
        }
    }
    
    next();
};

// Configuration Helmet avec paramètres personnalisés
const helmetConfig = helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com"],
            scriptSrc: ["'self'", "https://cdnjs.cloudflare.com"],
            imgSrc: ["'self'", "data:", "blob:"],
            fontSrc: ["'self'", "https://cdnjs.cloudflare.com"],
            connectSrc: ["'self'"],
            mediaSrc: ["'self'"],
            objectSrc: ["'none'"],
            childSrc: ["'self'"],
            frameAncestors: ["'none'"],
            formAction: ["'self'"],
            upgradeInsecureRequests: []
        }
    },
    crossOriginEmbedderPolicy: false, // Désactivé pour la compatibilité PDF
    hsts: {
        maxAge: 31536000,
        includeSubDomains: true,
        preload: true
    }
});

// Middleware de sécurité personnalisé
const customSecurityHeaders = (req, res, next) => {
    // Headers de sécurité supplémentaires
    res.setHeader('X-Download-Options', 'noopen');
    res.setHeader('X-Permitted-Cross-Domain-Policies', 'none');
    res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
    res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');
    
    next();
};

// Nettoyage des noms de fichiers
const sanitizeFilename = (filename) => {
    return filename
        .replace(/[^a-zA-Z0-9.-]/g, '_') // Remplacer les caractères spéciaux
        .replace(/_{2,}/g, '_') // Réduire les underscores multiples
        .substring(0, 100); // Limiter la longueur
};

module.exports = {
    rateLimiters,
    fileValidation,
    fileValidationMiddleware,
    suspiciousActivityDetector,
    helmetConfig,
    customSecurityHeaders,
    sanitizeFilename
};