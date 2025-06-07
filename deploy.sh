#!/bin/bash

# Script de déploiement final pour PDF Editor
set -e

DEPLOY_DIR="/opt/pdf-editor"
BACKUP_DIR="/backups/pdf-editor"
LOG_FILE="/var/log/pdf-editor-deploy.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Déploiement complet
deploy() {
    log "🚀 Début du déploiement PDF Editor"
    
    # Créer les répertoires nécessaires
    mkdir -p "$DEPLOY_DIR" "$BACKUP_DIR"
    cd "$DEPLOY_DIR"
    
    # Sauvegarder la version actuelle si elle existe
    if [ -f "docker-compose.prod.yml" ]; then
        log "💾 Sauvegarde de la version actuelle..."
        ./scripts/backup.sh || log "⚠️ Échec de la sauvegarde"
    fi
    
    # Arrêter les services existants
    log "⏹️ Arrêt des services..."
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    
    # Démarrer les nouveaux services
    log "▶️ Démarrage des services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    # Attendre que les services démarrent
    log "⏳ Attente du démarrage des services..."
    sleep 60
    
    # Exécuter les tests post-déploiement
    log "🧪 Exécution des tests post-déploiement..."
    if ./scripts/post-deploy-tests.sh; then
        log "✅ Tests réussis"
    else
        log "❌ Tests échoués - rollback recommandé"
        exit 1
    fi
    
    # Configurer les tâches cron
    log "⏰ Configuration des tâches automatisées..."
    setup_cron_jobs
    
    log "🎉 Déploiement terminé avec succès"
}

# Configuration des tâches cron
setup_cron_jobs() {
    # Sauvegarde quotidienne à 2h du matin
    (crontab -l 2>/dev/null; echo "0 2 * * * $DEPLOY_DIR/scripts/backup.sh") | crontab -
    
    # Maintenance hebdomadaire le dimanche à 3h du matin
    (crontab -l 2>/dev/null; echo "0 3 * * 0 $DEPLOY_DIR/scripts/maintenance.sh") | crontab -
    
    # Vérification de santé toutes les 5 minutes
    (crontab -l 2>/dev/null; echo "*/5 * * * * curl -f http://localhost/health >/dev/null 2>&1 || $DEPLOY_DIR/scripts/restart-services.sh") | crontab -
    
    log "✅ Tâches cron configurées"
}

# Exécuter le déploiement
deploy "$@"
