const request = require('supertest');
const app = require('../server');
const fs = require('fs');
const path = require('path');

describe('Performance Tests', () => {
    const testPdfPath = path.join(__dirname, 'fixtures', 'large-test.pdf');
    
    beforeAll(async () => {
        // Créer un PDF de test plus volumineux si nécessaire
        if (!fs.existsSync(testPdfPath)) {
            // Créer un PDF de test de 5MB
            await createLargePdfForTesting(testPdfPath);
        }
    });

    describe('File Upload Performance', () => {
        it('should handle large file upload within acceptable time', async () => {
            const startTime = Date.now();
            
            const response = await request(app)
                .post('/api/extract-pages')
                .attach('pdf', testPdfPath)
                .field('pages', JSON.stringify([1, 2, 3]))
                .expect(200);
            
            const duration = Date.now() - startTime;
            
            expect(duration).toBeLessThan(10000); // Moins de 10 secondes
            expect(response.headers['content-type']).toBe('application/pdf');
        }, 15000);

        it('should handle concurrent uploads', async () => {
            const concurrentRequests = 5;
            const promises = [];
            
            for (let i = 0; i < concurrentRequests; i++) {
                promises.push(
                    request(app)
                        .post('/api/extract-pages')
                        .attach('pdf', testPdfPath)
                        .field('pages', JSON.stringify([1]))
                );
            }
            
            const startTime = Date.now();
            const responses = await Promise.all(promises);
            const duration = Date.now() - startTime;
            
            // Toutes les requêtes doivent réussir
            responses.forEach(response => {
                expect(response.status).toBe(200);
            });
            
            // Le temps total ne doit pas être excessif
            expect(duration).toBeLessThan(30000); // Moins de 30 secondes
        }, 35000);
    });

    describe('Memory Usage', () => {
        it('should not cause memory leaks during multiple operations', async () => {
            const initialMemory = process.memoryUsage().heapUsed;
            
            // Effectuer plusieurs opérations
            for (let i = 0; i < 10; i++) {
                await request(app)
                    .post('/api/extract-pages')
                    .attach('pdf', testPdfPath)
                    .field('pages', JSON.stringify([1]))
                    .expect(200);
                
                // Forcer le garbage collection si disponible
                if (global.gc) {
                    global.gc();
                }
            }
            
            const finalMemory = process.memoryUsage().heapUsed;
            const memoryIncrease = finalMemory - initialMemory;
            
            // L'augmentation de mémoire ne doit pas être excessive
            expect(memoryIncrease).toBeLessThan(100 * 1024 * 1024); // Moins de 100MB
        }, 60000);
    });

    describe('Response Time Benchmarks', () => {
        const benchmarks = {
            'small-pdf': { size: '1MB', maxTime: 2000 },
            'medium-pdf': { size: '5MB', maxTime: 5000 },
            'large-pdf': { size: '10MB', maxTime: 10000 }
        };

        Object.entries(benchmarks).forEach(([type, config]) => {
            it(`should process ${type} (${config.size}) within ${config.maxTime}ms`, async () => {
                const startTime = Date.now();
                
                await request(app)
                    .post('/api/extract-pages')
                    .attach('pdf', testPdfPath)
                    .field('pages', JSON.stringify([1, 2]))
                    .expect(200);
                
                const duration = Date.now() - startTime;
                expect(duration).toBeLessThan(config.maxTime);
            }, config.maxTime + 5000);
        });
    });

    describe('Stress Testing', () => {
        it('should handle high load without crashing', async () => {
            const requests = 50;
            const batchSize = 10;
            const results = [];
            
            // Traiter par lots pour éviter de surcharger
            for (let i = 0; i < requests; i += batchSize) {
                const batch = [];
                const batchEnd = Math.min(i + batchSize, requests);
                
                for (let j = i; j < batchEnd; j++) {
                    batch.push(
                        request(app)
                            .get('/health')
                            .then(res => ({ success: res.status === 200 }))
                            .catch(err => ({ success: false, error: err.message }))
                    );
                }
                
                const batchResults = await Promise.all(batch);
                results.push(...batchResults);
                
                // Petite pause entre les lots
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            
            const successCount = results.filter(r => r.success).length;
            const successRate = (successCount / requests) * 100;
            
            expect(successRate).toBeGreaterThan(95); // Au moins 95% de succès
        }, 120000);
    });
});

// Utilitaire pour créer un PDF de test volumineux
async function createLargePdfForTesting(outputPath) {
    const PDFDocument = require('pdfkit');
    const fs = require('fs');
    
    return new Promise((resolve, reject) => {
        const doc = new PDFDocument();
        const stream = fs.createWriteStream(outputPath);
        
        doc.pipe(stream);
        
        // Créer plusieurs pages avec du contenu
        for (let page = 1; page <= 50; page++) {
            if (page > 1) doc.addPage();
            
            doc.fontSize(20).text(`Page ${page}`, 50, 50);
            
            // Ajouter du contenu pour augmenter la taille
            for (let i = 0; i < 100; i++) {
                doc.fontSize(12).text(
                    `Ligne ${i + 1}: Lorem ipsum dolor sit amet, consectetur adipiscing elit. ` +
                    `Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.`,
                    50,
                    100 + (i * 15)
                );
            }
        }
        
        doc.end();
        
        stream.on('finish', resolve);
        stream.on('error', reject);
    });
}