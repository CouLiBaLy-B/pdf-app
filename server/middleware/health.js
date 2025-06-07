const os = require('os');
const fs = require('fs').promises;
const path = require('path');

class HealthChecker {
    constructor() {
        this.checks = new Map();
        this.setupDefaultChecks();
    }

    setupDefaultChecks() {
        // Vérification de la base de données
        this.addCheck('database', async () => {
            // Simuler une vérification de DB
            return { status: 'healthy', latency: 5 };
        });

        // Vérification du système de fichiers
        this.addCheck('filesystem', async () => {
            try {
                const uploadsDir = path.join(__dirname, '../../uploads');
                await fs.access(uploadsDir);
                const stats = await fs.stat(uploadsDir);
                return { 
                    status: 'healthy', 
                    writable: true,
                    size: stats.size 
                };
            } catch (error) {
                return { 
                    status: 'unhealthy', 
                    error: error.message 
                };
            }
        });

        // Vérification de la mémoire
        this.addCheck('memory', async () => {
            const usage = process.memoryUsage();
            const total = os.totalmem();
            const free = os.freemem();
            const usedPercent = ((total - free) / total) * 100;

            return {
                status: usedPercent > 90 ? 'warning' : 'healthy',
                heap: {
                    used: Math.round(usage.heapUsed / 1024 / 1024),
                    total: Math.round(usage.heapTotal / 1024 / 1024)
                },
                system: {
                    used: Math.round(usedPercent),
                    free: Math.round(free / 1024 / 1024),
                    total: Math.round(total / 1024 / 1024)
                }
            };
        });

        // Vérification du CPU
        this.addCheck('cpu', async () => {
            const cpus = os.cpus();
            const loadAvg = os.loadavg();
            
            return {
                status: loadAvg[0] > cpus.length ? 'warning' : 'healthy',
                cores: cpus.length,
                loadAverage: {
                    '1min': Math.round(loadAvg[0] * 100) / 100,
                    '5min': Math.round(loadAvg[1] * 100) / 100,
                    '15min': Math.round(loadAvg[2] * 100) / 100
                }
            };
        });

        // Vérification de l'uptime
        this.addCheck('uptime', async () => {
            const uptime = process.uptime();
            return {
                status: 'healthy',
                uptime: Math.floor(uptime),
                formatted: this.formatUptime(uptime)
            };
        });
    }

    addCheck(name, checkFunction) {
        this.checks.set(name, checkFunction);
    }

    async runAllChecks() {
        const results = {};
        const promises = [];

        for (const [name, checkFn] of this.checks) {
            promises.push(
                this.runSingleCheck(name, checkFn)
                    .then(result => ({ name, result }))
                    .catch(error => ({ 
                        name, 
                        result: { 
                            status: 'error', 
                            error: error.message 
                        } 
                    }))
            );
        }

        const checkResults = await Promise.all(promises);
        
        for (const { name, result } of checkResults) {
            results[name] = result;
        }

        // Déterminer le statut global
        const statuses = Object.values(results).map(r => r.status);
        let overallStatus = 'healthy';
        
        if (statuses.includes('error') || statuses.includes('unhealthy')) {
            overallStatus = 'unhealthy';
        } else if (statuses.includes('warning')) {
            overallStatus = 'warning';
        }

        return {
            status: overallStatus,
            timestamp: new Date().toISOString(),
            version: process.env.npm_package_version || '1.0.0',
            environment: process.env.NODE_ENV || 'development',
            checks: results
        };
    }

    async runSingleCheck(name, checkFn) {
        const start = Date.now();
        try {
            const result = await Promise.race([
                checkFn(),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Timeout')), 5000)
                )
            ]);
            
            return {
                ...result,
                duration: Date.now() - start
            };
        } catch (error) {
            return {
                status: 'error',
                error: error.message,
                duration: Date.now() - start
            };
        }
    }

    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (days > 0) {
            return `${days}d ${hours}h ${minutes}m`;
        } else if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else {
            return `${minutes}m`;
        }
    }
}

// Middleware Express pour le health check
const healthChecker = new HealthChecker();

const healthMiddleware = async (req, res) => {
    try {
        const health = await healthChecker.runAllChecks();
        
        // Définir le code de statut HTTP basé sur la santé
        let statusCode = 200;
        if (health.status === 'warning') {
            statusCode = 200; // Toujours 200 pour les warnings
        } else if (health.status === 'unhealthy' || health.status === 'error') {
            statusCode = 503; // Service Unavailable
        }
        
        res.status(statusCode).json(health);
    } catch (error) {
        res.status(500).json({
            status: 'error',
            error: 'Health check failed',
            message: error.message,
            timestamp: new Date().toISOString()
        });
    }
};

module.exports = {
    HealthChecker,
    healthMiddleware,
    healthChecker
};