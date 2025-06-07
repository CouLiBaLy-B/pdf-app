const winston = require('winston');
const path = require('path');

// Configuration des formats de log
const logFormat = winston.format.combine(
    winston.format.timestamp({
        format: 'YYYY-MM-DD HH:mm:ss'
    }),
    winston.format.errors({ stack: true }),
    winston.format.json()
);

const consoleFormat = winston.format.combine(
    winston.format.colorize(),
    winston.format.timestamp({
        format: 'HH:mm:ss'
    }),
    winston.format.printf(({ timestamp, level, message, ...meta }) => {
        let msg = `${timestamp} [${level}] ${message}`;
        if (Object.keys(meta).length > 0) {
            msg += ` ${JSON.stringify(meta)}`;
        }
        return msg;
    })
);

// Créer le logger
const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: logFormat,
    defaultMeta: { 
        service: 'pdf-editor',
        version: process.env.npm_package_version || '1.0.0'
    },
    transports: [
        // Fichier pour toutes les erreurs
        new winston.transports.File({
            filename: path.join(process.env.LOG_DIR || './logs', 'error.log'),
            level: 'error',
            maxsize: 5242880, // 5MB
            maxFiles: 5,
            tailable: true
        }),
        
        // Fichier pour tous les logs
        new winston.transports.File({
            filename: path.join(process.env.LOG_DIR || './logs', 'combined.log'),
            maxsize: 5242880, // 5MB
            maxFiles: 10,
            tailable: true
        }),
        
        // Fichier pour les opérations PDF
        new winston.transports.File({
            filename: path.join(process.env.LOG_DIR || './logs', 'pdf-operations.log'),
            level: 'info',
            maxsize: 5242880,
            maxFiles: 5,
            tailable: true,
            format: winston.format.combine(
                winston.format.timestamp(),
                winston.format.json(),
                winston.format((info) => {
                    return info.operation ? info : false;
                })()
            )
        })
    ]
});

// Ajouter la console en développement
if (process.env.NODE_ENV !== 'production') {
    logger.add(new winston.transports.Console({
        format: consoleFormat
    }));
}

// Middleware Express pour logger les requêtes
const requestLogger = (req, res, next) => {
    const start = Date.now();
    
    // Logger la requête entrante
    logger.info('Incoming request', {
        method: req.method,
        url: req.url,
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        requestId: req.id
    });
    
    // Logger la réponse
    res.on('finish', () => {
        const duration = Date.now() - start;
        const logLevel = res.statusCode >= 400 ? 'warn' : 'info';
        
        logger.log(logLevel, 'Request completed', {
            method: req.method,
            url: req.url,
            statusCode: res.statusCode,
            duration: `${duration}ms`,
            contentLength: res.get('Content-Length'),
            requestId: req.id
        });
    });
    
    next();
};

// Logger spécialisé pour les opérations PDF
const pdfLogger = {
    operation: (operation, metadata = {}) => {
        logger.info('PDF operation', {
            operation,
            timestamp: new Date().toISOString(),
            ...metadata
        });
    },
    
    error: (operation, error, metadata = {}) => {
        logger.error('PDF operation failed', {
            operation,
            error: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString(),
            ...metadata
        });
    },
    
    performance: (operation, duration, metadata = {}) => {
        logger.info('PDF operation performance', {
            operation,
            duration: `${duration}ms`,
            timestamp: new Date().toISOString(),
            ...metadata
        });
    }
};

// Logger pour les métriques de sécurité
const securityLogger = {
    suspiciousActivity: (activity, req, metadata = {}) => {
        logger.warn('Suspicious activity detected', {
            activity,
            ip: req.ip,
            userAgent: req.get('User-Agent'),
            url: req.url,
            timestamp: new Date().toISOString(),
            ...metadata
        });
    },
    
    rateLimitExceeded: (req) => {
        logger.warn('Rate limit exceeded', {
            ip: req.ip,
            userAgent: req.get('User-Agent'),
            url: req.url,
            timestamp: new Date().toISOString()
        });
    },
    
    fileUploadRejected: (reason, req, fileInfo = {}) => {
        logger.warn('File upload rejected', {
            reason,
            ip: req.ip,
            fileName: fileInfo.originalname,
            fileSize: fileInfo.size,
            mimeType: fileInfo.mimetype,
            timestamp: new Date().toISOString()
        });
    }
};

module.exports = {
    logger,
    requestLogger,
    pdfLogger,
    securityLogger
};