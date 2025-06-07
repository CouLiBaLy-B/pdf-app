const request = require('supertest');
const app = require('../server');
const fs = require('fs');
const path = require('path');

describe('PDF Editor API', () => {
    const testPdfPath = path.join(__dirname, 'test.pdf');
    
    beforeAll(() => {
        // Créer un PDF de test simple si nécessaire
        if (!fs.existsSync(testPdfPath)) {
            // Créer un PDF minimal pour les tests
            const PDFDocument = require('pdfkit');
            const doc = new PDFDocument();
            doc.pipe(fs.createWriteStream(testPdfPath));
            doc.text('Test PDF pour les tests unitaires');
            doc.end();
        }
    });

    describe('POST /api/extract-pages', () => {
        it('devrait extraire les pages spécifiées', async () => {
            const response = await request(app)
                .post('/api/extract-pages')
                .attach('pdf', testPdfPath)
                .field('pages', JSON.stringify([1]))
                .expect(200);

            expect(response.headers['content-type']).toBe('application/pdf');
        });

        it('devrait retourner une erreur pour des pages invalides', async () => {
            const response = await request(app)
                .post('/api/extract-pages')
                .attach('pdf', testPdfPath)
                .field('pages', JSON.stringify([999]))
                .expect(500);
        });
    });

    describe('POST /api/merge-pdfs', () => {
        it('devrait fusionner plusieurs PDFs', async () => {
            const response = await request(app)
                .post('/api/merge-pdfs')
                .attach('pdfs', testPdfPath)
                .attach('pdfs', testPdfPath)
                .expect(200);

            expect(response.headers['content-type']).toBe('application/pdf');
        });
    });

    describe('POST /api/rotate-pages', () => {
        it('devrait faire tourner les pages spécifiées', async () => {
            const response = await request(app)
                .post('/api/rotate-pages')
                .attach('pdf', testPdfPath)
                .field('pages', JSON.stringify([1]))
                .field('angle', '90')
                .expect(200);

            expect(response.headers['content-type']).toBe('application/pdf');
        });
    });

    describe('POST /api/compress-pdf', () => {
        it('devrait compresser le PDF', async () => {
            const response = await request(app)
                .post('/api/compress-pdf')
                .attach('pdf', testPdfPath)
                .field('level', 'medium')
                .expect(200);

            expect(response.headers['content-type']).toBe('application/pdf');
        });
    });

    afterAll(() => {
        // Nettoyer les fichiers de test
        if (fs.existsSync(testPdfPath)) {
            fs.unlinkSync(testPdfPath);
        }
    });
});