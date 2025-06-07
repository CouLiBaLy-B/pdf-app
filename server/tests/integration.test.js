const request = require('supertest');
const app = require('../server');
const fs = require('fs');
const path = require('path');

describe('Integration Tests', () => {
    const testPdfPath = path.join(__dirname, 'fixtures', 'test.pdf');
    
    beforeAll(() => {
        // S'assurer que le fichier de test existe
        if (!fs.existsSync(testPdfPath)) {
            throw new Error('Test PDF file not found');
        }
    });

    describe('Complete PDF Processing Workflow', () => {
        it('should handle complete extraction workflow', async () => {
            // 1. Upload et extraction de pages
            const extractResponse = await request(app)
                .post('/api/extract-pages')
                .attach('pdf', testPdfPath)
                .field('pages', JSON.stringify([1, 2]))
                .expect(200);

            expect(extractResponse.headers['content-type']).toBe('application/pdf');
            expect(extractResponse.body.length).toBeGreaterThan(0);

            // 2. Vérifier que le PDF extrait est valide
            const tempPath = path.join(__dirname, 'temp', 'extracted.pdf');
            fs.writeFileSync(tempPath, extractResponse.body);
            
            // 3. Utiliser le PDF extrait pour une nouvelle opération
            const mergeResponse = await request(app)
                .post('/api/merge-pdfs')
                .attach('pdfs', testPdfPath)
                .attach('pdfs', tempPath)
                .expect(200);

            expect(mergeResponse.headers['content-type']).toBe('application/pdf');
            
            // Nettoyage
            fs.unlinkSync(tempPath);
        });

        it('should handle text extraction and modification workflow', async () => {
            // 1. Extraire le texte
            const textResponse = await request(app)
                .post('/api/extract-text')
                .attach('pdf', testPdfPath)
                .expect(200);

            expect(textResponse.body).toHaveProperty('text');
            expect(typeof textResponse.body.text).toBe('string');

            // 2. Ajouter du texte au PDF
            const modifyResponse = await request(app)
                .post('/api/add-text')
                .attach('pdf', testPdfPath)
                .field('text', 'Texte ajouté par test')
                .field('x', '100')
                .field('y', '100')
                .field('page', '1')
                .expect(200);

            expect(modifyResponse.headers['content-type']).toBe('application/pdf');
        });
    });

    describe('Error Handling Integration', () => {
        it('should handle invalid file gracefully', async () => {
            const invalidFilePath = path.join(__dirname, 'fixtures', 'invalid.txt');
            fs.writeFileSync(invalidFilePath, 'This is not a PDF');

            const response = await request(app)
                .post('/api/extract-pages')
                .attach('pdf', invalidFilePath)
                .field('pages', JSON.stringify([1]))
                .expect(400);

            expect(response.body).toHaveProperty('error');
            
            // Nettoyage
            fs.unlinkSync(invalidFilePath);
        });

        it('should handle malformed requests', async () => {
            const response = await request(app)
                .post('/api/extract-pages')
                .attach('pdf', testPdfPath)
                .field('pages', 'invalid-json')
                .expect(400);

            expect(response.body).toHaveProperty('error');
        });
    });

    describe('Security Integration Tests', () => {
        it('should reject files that are too large', async () => {
            // Créer un fichier factice très volumineux
            const largePath = path.join(__dirname, 'temp', 'large.pdf');
            const largeBuffer = Buffer.alloc(60 * 1024 * 1024); // 60MB
            fs.writeFileSync(largePath, largeBuffer);

            const response = await request(app)
                .post('/api/extract-pages')
                .attach('pdf', largePath)
                .field('pages', JSON.stringify([1]))
                .expect(400);

            expect(response.body.error).toContain('trop volumineux');
            
            // Nettoyage
            fs.unlinkSync(largePath);
        });

        it('should enforce rate limiting', async () => {
            const requests = [];
            
            // Faire plus de requêtes que la limite autorisée
            for (let i = 0; i < 10; i++) {
                requests.push(
                    request(app)
                        .get('/health')
                        .then(res => res.status)
                        .catch(err => err.status)
                );
            }

            const responses = await Promise.all(requests);
            
            // Au moins une requête devrait être limitée
            expect(responses).toContain(429);
        });
    });

    describe('Performance Integration', () => {
        it('should maintain performance under load', async () => {
            const concurrentRequests = 5;
            const promises = [];

            for (let i = 0; i < concurrentRequests; i++) {
                promises.push(
                    request(app)
                        .post('/api/extract-text')
                        .attach('pdf', testPdfPath)
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
            expect(duration).toBeLessThan(15000); // 15 secondes max
        });
    });
});