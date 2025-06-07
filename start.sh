#!/bin/bash

# Script de déploiement automatisé pour PDF Editor
set -e

# Configuration
REPO_URL="https://github.com/coulibaly-b/pdf-editor.git"
DEPLOY_DIR="/opt/pdf-editor"
BACKUP_DIR="./backups/pdf-editor"
LOG_DIR="./logs"

LOG_FILE="$LOG_DIR/pdf-editor-deploy.log"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
EMAIL_RECIPIENT="${EMAIL_RECIPIENT:-admin@yourdomain.com}"

# Créer les répertoires nécessaires
mkdir -p "$LOG_DIR" "$BACKUP_DIR"

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${GREEN}[INFO]${NC} ${timestamp} - $message" | tee -a "$LOG_FILE"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} ${timestamp} - $message" | tee -a "$LOG_FILE"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} ${timestamp} - $message" | tee -a "$LOG_FILE"
            ;;
        "DEBUG")
            echo -e "${BLUE}[DEBUG]${NC} ${timestamp} - $message" | tee -a "$LOG_FILE"
            ;;
    esac
}

send_notification() {
    local status=$1
    local message=$2
    
    # Notification Slack
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        local color="good"
        [ "$status" = "error" ] && color="danger"
        [ "$status" = "warning" ] && color="warning"
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"title\":\"PDF Editor Deployment\",\"text\":\"$message\"}]}" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || true
    fi
    
    # Notification email
    if command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "PDF Editor Deployment - $status" "$EMAIL_RECIPIENT" 2>/dev/null || true
    fi
}

check_prerequisites() {
    log "INFO" "🔍 Vérification des prérequis..."
    
    local missing_tools=()
    
    for tool in "docker" "docker-compose" "git" "curl"; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            missing_tools+=("$tool")
        fi
    done
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log "ERROR" "Outils manquants: ${missing_tools[*]}"
        exit 1
    fi
    
    # Vérifier que Docker fonctionne
    if ! docker info >/dev/null 2>&1; then
        log "ERROR" "Docker n'est pas accessible"
        exit 1
    fi
    
    log "INFO" "✅ Tous les prérequis sont satisfaits"
}

create_backup() {
    log "INFO" "💾 Création de la sauvegarde..."
    
    local backup_name="backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    mkdir -p "$BACKUP_DIR"
    
    # Sauvegarder la configuration et les données
    tar -czf "$backup_path" \
        -C "$DEPLOY_DIR" \
        --exclude='node_modules' \
        --exclude='logs' \
        --exclude='temp' \
        . 2>/dev/null || true
    
    # Sauvegarder les volumes Docker
    docker run --rm \
        -v pdf-editor_uploads_data:/data \
        -v "$BACKUP_DIR:/backup" \
        alpine tar -czf "/backup/uploads-$backup_name" -C /data . 2>/dev/null || true
    
    log "INFO" "✅ Sauvegarde créée: $backup_path"
    echo "$backup_path" # Retourner le chemin pour usage ultérieur
}

deploy_application() {
    log "INFO" "🚀 Déploiement de l'application..."
    
    cd "$DEPLOY_DIR"
    
    # Récupérer les dernières modifications
    log "INFO" "📥 Récupération du code source..."
    git fetch origin
    local current_commit=$(git rev-parse HEAD)
    local latest_commit=$(git rev-parse origin/main)
    
    if [ "$current_commit" = "$latest_commit" ]; then
        log "INFO" "ℹ️ Aucune mise à jour disponible"
        return 0
    fi
    
    log "INFO" "🔄 Mise à jour de $current_commit vers $latest_commit"
    git reset --hard origin/main
    
    # Construire les nouvelles images
    log "INFO" "🏗️ Construction des images Docker..."
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # Démarrer les nouveaux conteneurs
    log "INFO" "🔄 Redémarrage des services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    log "INFO" "✅ Déploiement terminé"
}

run_health_checks() {
    log "INFO" "🏥 Vérification de la santé de l'application..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log "DEBUG" "Tentative $attempt/$max_attempts..."
        
        if curl -f http://localhost:3000/health >/dev/null 2>&1; then
            log "INFO" "✅ Application en bonne santé"
            return 0
        fi
        
        sleep 10
        ((attempt++))
    done
    
    log "ERROR" "❌ L'application ne répond pas après $max_attempts tentatives"
    return 1
}

run_smoke_tests() {
    log "INFO" "🧪 Exécution des tests de fumée..."
    
    local test_pdf="test-files/sample.pdf"
    local temp_dir=$(mktemp -d)
    
    # Test 1: Upload et extraction
    log "DEBUG" "Test d'extraction de pages..."
    if curl -f -X POST \
        -F "pdf=@$test_pdf" \
        -F "pages=[1]" \
        http://localhost:3000/api/extract-pages \
        -o "$temp_dir/extracted.pdf" 2>/dev/null; then
        log "INFO" "✅ Test d'extraction réussi"
    else
        log "ERROR" "❌ Test d'extraction échoué"
        rm -rf "$temp_dir"
        return 1
    fi
    
    # Test 2: Extraction de texte
    log "DEBUG" "Test d'extraction de texte..."
    if curl -f -X POST \
        -F "pdf=@$test_pdf" \
        http://localhost:3000/api/extract-text 2>/dev/null | grep -q "text"; then
        log "INFO" "✅ Test d'extraction de texte réussi"
    else
        log "ERROR" "❌ Test d'extraction de texte échoué"
        rm -rf "$temp_dir"
        return 1
    fi
    
    rm -rf "$temp_dir"
    log "INFO" "✅ Tous les tests de fumée sont passés"
}

rollback() {
    local backup_path=$1
    log "WARN" "🔄 Rollback en cours..."
    
    cd "$DEPLOY_DIR"
    
    # Arrêter les services
    docker-compose -f docker-compose.prod.yml down
    
    # Restaurer la sauvegarde
    if [ -f "$backup_path" ]; then
        tar -xzf "$backup_path" -C "$DEPLOY_DIR"
        log "INFO" "✅ Sauvegarde restaurée"
    else
        log "ERROR" "❌ Sauvegarde non trouvée: $backup_path"
        # Revenir au commit précédent
        git reset --hard HEAD~1
    fi
    
    # Redémarrer les services
    docker-compose -f docker-compose.prod.yml up -d
    
    # Attendre que les services redémarrent
    sleep 30
    
    if run_health_checks; then
        log "INFO" "✅ Rollback réussi"
        send_notification "warning" "Déploiement échoué, rollback effectué avec succès"
    else
        log "ERROR" "❌ Rollback échoué"
        send_notification "error" "Déploiement ET rollback échoués - intervention manuelle requise"
        exit 1
    fi
}

cleanup() {
    log "INFO" "🧹 Nettoyage..."
    
    # Supprimer les images Docker inutilisées
    docker image prune -f
    
    # Supprimer les anciennes sauvegardes (garder les 10 dernières)
    find "$BACKUP_DIR" -name "backup-*.tar.gz" -type f | \
        sort -r | tail -n +11 | xargs rm -f 2>/dev/null || true
    
    log "INFO" "✅ Nettoyage terminé"
}

main() {
    local start_time=$(date +%s)
    
    log "INFO" "🚀 Début du déploiement PDF Editor"
    
    # Vérifications préliminaires
    check_prerequisites
    
    # Créer une sauvegarde
    local backup_path
    backup_path=$(create_backup)
    
    # Déployer l'application
    if deploy_application; then
        log "INFO" "✅ Déploiement réussi"
    else
        log "ERROR" "❌ Échec du déploiement"
        rollback "$backup_path"
        exit 1
    fi
    
    # Vérifications post-déploiement
    if ! run_health_checks; then
        log "ERROR" "❌ Vérifications de santé échouées"
        rollback "$backup_path"
        exit 1
    fi
    
    if ! run_smoke_tests; then
        log "ERROR" "❌ Tests de fumée échoués"
        rollback "$backup_path"
        exit 1
    fi
    
    # Nettoyage
    cleanup
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log "INFO" "🎉 Déploiement terminé avec succès en ${duration}s"
    send_notification "good" "Déploiement PDF Editor réussi en ${duration}s"
}

# Gestion des signaux pour nettoyage en cas d'interruption
trap 'log "WARN" "Déploiement interrompu"; exit 1' INT TERM

# Point d'entrée
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
