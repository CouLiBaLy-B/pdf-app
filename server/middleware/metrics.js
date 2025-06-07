const client = require('prom-client');

// Créer un registre pour les métriques
const register = new client.Registry();

// Métriques par défaut de Node.js
client.collectDefaultMetrics({ register });

// Compteur de requêtes HTTP
const httpRequestsTotal = new client.Counter({
    name: 'http_requests_total',
    help: 'Total number of HTTP requests',
    labelNames: ['method', 'status_code', 'route'],
    registers: [register]
});

// Histogramme des temps de réponse
const httpRequestDuration = new client.Histogram({
    name: 'http_request_duration_seconds',
    help: 'Duration of HTTP requests in seconds',
    labelNames: ['method', 'status_code', 'route'],
    buckets: [0.1, 0.5, 1, 2, 5, 10],
    registers: [register]
});

// Compteur d'opérations PDF
const pdfOperationsTotal = new client.Counter({
    name: 'pdf_operations_total',
    help: 'Total number of PDF operations',
    labelNames: ['operation', 'status'],
    registers: [register]
});

// Histogramme des temps d'opération PDF
const pdfOperationDuration = new client.Histogram({
    name: 'pdf_operation_duration_seconds',
    help: 'Duration of PDF operations in seconds',
    labelNames: ['operation'],
    buckets: [0.5, 1, 2, 5, 10, 30],
    registers: [register]
});

// Gauge pour l'utilisation mémoire
const memoryUsage = new client.Gauge({
    name: 'memory_usage_bytes',
    help: 'Memory usage in bytes',
    labelNames: ['type'],
    registers: [register]
});

// Gauge pour les connexions actives
const activeConnections = new client.Gauge({
    name: 'active_connections',
    help: 'Number of active connections',
    registers: [register]
});

// Gauge pour l'uptime du processus
const processUptime = new client.Gauge({
    name: 'process_uptime_seconds',
    help: 'Process uptime in seconds',
    registers: [register]
});

// Middleware pour collecter les métriques HTTP
const metricsMiddleware = (req, res, next) => {
    const start = Date.now();
  
    res.on('finish', () => {
      const duration = (Date.now() - start) / 1000;
      const route = req.route ? req.route.path : req.path;
    
      httpRequestsTotal
        .labels(req.method, res.statusCode.toString(), route)
        .inc();
    
      httpRequestDuration
        .labels(req.method, res.statusCode.toString(), route)
        .observe(duration);
    });
  
    next();
};

// Fonction pour enregistrer une opération PDF
const recordPdfOperation = (operation, status, duration) => {
    pdfOperationsTotal
      .labels(operation, status)
      .inc();
  
    if (duration !== undefined) {
      pdfOperationDuration
        .labels(operation)
        .observe(duration / 1000);
    }
};

// Mise à jour périodique des métriques système
const updateSystemMetrics = () => {
    const usage = process.memoryUsage();
  
    memoryUsage.labels('heapUsed').set(usage.heapUsed);
    memoryUsage.labels('heapTotal').set(usage.heapTotal);
    memoryUsage.labels('external').set(usage.external);
    memoryUsage.labels('rss').set(usage.rss);
  
    processUptime.set(process.uptime());
};

// Mettre à jour les métriques système toutes les 10 secondes
setInterval(updateSystemMetrics, 10000);

// Endpoint pour exposer les métriques
const metricsEndpoint = async (req, res) => {
    try {
      res.set('Content-Type', register.contentType);
      res.end(await register.metrics());
    } catch (error) {
      res.status(500).end(error.message);
    }
};

// Fonction pour incrémenter les connexions actives
const incrementActiveConnections = () => {
    activeConnections.inc();
};

// Fonction pour décrémenter les connexions actives
const decrementActiveConnections = () => {
    activeConnections.dec();
};

module.exports = {
    register,
    metricsMiddleware,
    metricsEndpoint,
    recordPdfOperation,
    incrementActiveConnections,
    decrementActiveConnections,
    updateSystemMetrics,
    // Exposer les métriques individuelles pour usage externe
    metrics: {
        httpRequestsTotal,
        httpRequestDuration,
        pdfOperationsTotal,
        pdfOperationDuration,
        memoryUsage,
        activeConnections,
        processUptime
    }
};
