#!/bin/bash

# Tests post-déploiement pour PDF Editor
set -e

BASE_URL="${BASE_URL:-http://localhost:3000}"
TEST_FILES_DIR="test-files"
LOG_FILE="/var/log/pdf-editor-post-deploy.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Test de santé de base
test_health_endpoint() {
    log "🏥 Test de l'endpoint de santé..."
    
    local response
    response=$(curl -s -w "%{http_code}" "$BASE_URL/health")
    local http_code="${response: -3}"
    
    if [ "$http_code" = "200" ]; then
        log "✅ Endpoint de santé OK"
        return 0
    else
        log "❌ Endpoint de santé échoué (code: $http_code)"
        return 1
    fi
}

# Test des métriques
test_metrics_endpoint() {
    log "📊 Test de l'endpoint des métriques..."
    
    local response
    response=$(curl -s -w "%{http_code}" "$BASE_URL/metrics")
    local http_code="${response: -3}"
    
    if [ "$http_code" = "200" ] && echo "$response" | grep -q "http_requests_total"; then
        log "✅ Endpoint des métriques OK"
        return 0
    else
        log "❌ Endpoint des métriques échoué"
        return 1
    fi
}

# Test d'extraction de pages
test_page_extraction() {
    log "📄 Test d'extraction de pages..."
    
    local test_pdf="$TEST_FILES_DIR/sample.pdf"
    local temp_file=$(mktemp)
    
    if [ ! -f "$test_pdf" ]; then
        log "⚠️ Fichier de test non trouvé: $test_pdf"
        return 1
    fi
    
    local response
    response=$(curl -s -w "%{http_code}" \
        -X POST \
        -F "pdf=@$test_pdf" \
        -F "pages=[1,2]" \
        "$BASE_URL/api/extract-pages" \
        -o "$temp_file")
    
    local http_code="${response: -3}"
    
    if [ "$http_code" = "200" ] && [ -s "$temp_file" ]; then
        log "✅ Extraction de pages OK"
        rm -f "$temp_file"
        return 0
    else
        log "❌ Extraction de pages échouée (code: $http_code)"
        rm -f "$temp_file"
        return 1
    fi
}

# Test d'extraction de texte
test_text_extraction() {
    log "📝 Test d'extraction de texte..."
    
    local test_pdf="$TEST_FILES_DIR/sample.pdf"
    
    if [ ! -f "$test_pdf" ]; then
        log "⚠️ Fichier de test non trouvé: $test_pdf"
        return 1
    fi
    
    local response
    response=$(curl -s -w "%{http_code}" \
        -X POST \
        -F "pdf=@$test_pdf" \
        "$BASE_URL/api/extract-text")
    
    local http_code="${response: -3}"
    local body="${response%???}"
    
    if [ "$http_code" = "200" ] && echo "$body" | jq -e '.text' >/dev/null 2>&1; then
        log "✅ Extraction de texte OK"
        return 0
    else
        log "❌ Extraction de texte échouée (code: $http_code)"
        return 1
    fi
}

# Test de fusion de PDF
test_pdf_merge() {
    log "🔗 Test de fusion de PDF..."
    
    local test_pdf1="$TEST_FILES_DIR/sample.pdf"
    local test_pdf2="$TEST_FILES_DIR/sample2.pdf"
    local temp_file=$(mktemp)
    
    # Créer un second fichier de test si nécessaire
    if [ ! -f "$test_pdf2" ]; then
        cp "$test_pdf1" "$test_pdf2" 2>/dev/null || {
            log "⚠️ Impossible de créer le second fichier de test"
            return 1
        }
    fi
    
    local response
    response=$(curl -s -w "%{http_code}" \
        -X POST \
        -F "pdfs=@$test_pdf1" \
        -F "pdfs=@$test_pdf2" \
        "$BASE_URL/api/merge-pdfs" \
        -o "$temp_file")
    
    local http_code="${response: -3}"
    
    if [ "$http_code" = "200" ] && [ -s "$temp_file" ]; then
        log "✅ Fusion de PDF OK"
        rm -f "$temp_file"
        return 0
    else
        log "❌ Fusion de PDF échouée (code: $http_code)"
        rm -f "$temp_file"
        return 1
    fi
}

# Test de performance
test_performance() {
    log "⚡ Test de performance..."
    
    local start_time=$(date +%s%N)
    
    # Faire plusieurs requêtes simultanées
    for i in {1..5}; do
        curl -s "$BASE_URL/health" >/dev/null &
    done
    
    wait
    
    local end_time=$(date +%s%N)
    local duration=$(( (end_time - start_time) / 1000000 )) # en millisecondes
    
    if [ $duration -lt 5000 ]; then # moins de 5 secondes
        log "✅ Test de performance OK (${duration}ms)"
        return 0
    else
        log "❌ Test de performance échoué (${duration}ms)"
        return 1
    fi
}

# Test de limite de taille de fichier
test_file_size_limit() {
    log "📏 Test de limite de taille de fichier..."
    
    local large_file=$(mktemp)
    dd if=/dev/zero of="$large_file" bs=1M count=60 2>/dev/null # 60MB
    
    local response
    response=$(curl -s -w "%{http_code}" \
        -X POST \
        -F "pdf=@$large_file" \
        -F "pages=[1]" \
        "$BASE_URL/api/extract-pages" 2>/dev/null)
    
    local http_code="${response: -3}"
    
    rm -f "$large_file"
    
    if [ "$http_code" = "400" ] || [ "$http_code" = "413" ]; then
        log "✅ Limite de taille de fichier OK"
        return 0
    else
        log "❌ Limite de taille de fichier non respectée (code: $http_code)"
        return 1
    fi
}

# Test de sécurité basique
test_security() {
    log "🔒 Test de sécurité basique..."
    
    # Test d'injection de commande
    local response
    response=$(curl -s -w "%{http_code}" \
        -X POST \
        -F "pdf=@/etc/passwd" \
        "$BASE_URL/api/extract-text" 2>/dev/null)
    
    local http_code="${response: -3}"
    
    if [ "$http_code" = "400" ] || [ "$http_code" = "415" ]; then
        log "✅ Test de sécurité OK"
        return 0
    else
        log "❌ Problème de sécurité détecté (code: $http_code)"
        return 1
    fi
}

# Fonction principale
main() {
    log "🚀 Début des tests post-déploiement"
    
    local failed_tests=0
    local total_tests=0
    
    # Liste des tests à exécuter
    local tests=(
        "test_health_endpoint"
        "test_metrics_endpoint"
        "test_page_extraction"
        "test_text_extraction"
        "test_pdf_merge"
        "test_performance"
        "test_file_size_limit"
        "test_security"
    )
    
    # Exécuter chaque test
    for test in "${tests[@]}"; do
        ((total_tests++))
        if ! $test; then
            ((failed_tests++))
        fi
        sleep 1 # Petite pause entre les tests
    done
    
    # Résumé
    local passed_tests=$((total_tests - failed_tests))
    log "📊 Résumé: $passed_tests/$total_tests tests réussis"
    
    if [ $failed_tests -eq 0 ]; then
        log "🎉 Tous les tests post-déploiement sont passés"
        exit 0
    else
        log "❌ $failed_tests test(s) échoué(s)"
        exit 1
    fi
}

# Créer le répertoire de test s'il n'existe pas
mkdir -p "$TEST_FILES_DIR"

# Créer un fichier PDF de test simple si nécessaire
if [ ! -f "$TEST_FILES_DIR/sample.pdf" ]; then
    log "📄 Création d'un fichier PDF de test..."
    
    # Utiliser Python pour créer un PDF simple
    python3 -c "
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os

os.makedirs('$TEST_FILES_DIR', exist_ok=True)
c = canvas.Canvas('$TEST_FILES_DIR/sample.pdf', pagesize=letter)
c.drawString(100, 750, 'Test PDF for post-deployment testing')
c.drawString(100, 700, 'This is page 1')
c.showPage()
c.drawString(100, 750, 'This is page 2')
c.save()
" 2>/dev/null || {
        log "⚠️ Impossible de créer le fichier PDF de test"
        # Créer un fichier factice pour les tests qui ne nécessitent pas un vrai PDF
        echo "Fake PDF content" > "$TEST_FILES_DIR/sample.pdf"
    }
fi

# Exécuter les tests
main "$@"
