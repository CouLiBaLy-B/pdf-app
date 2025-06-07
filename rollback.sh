#!/bin/bash

# Script de rollback automatisé
set -e

BACKUP_DIR="/backups/pdf-editor"
LOG_FILE="/var/log/pdf-editor-rollback.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error_exit() {
    log "ERREUR: $1"
    exit 1
}

# Lister les sauvegardes disponibles
log "📋 Sauvegardes disponibles:"
ls -la "$BACKUP_DIR"/*.tar.gz 2>/dev/null || error_exit "Aucune sauvegarde trouvée"

# Sélection de la sauvegarde
if [ -z "$1" ]; then
    echo "Usage: $0 <fichier-sauvegarde>"
    echo "Exemple: $0 backup-20240115-143022.tar.gz"
    exit 1
fi

BACKUP_FILE="$BACKUP_DIR/$1"
if [ ! -f "$BACKUP_FILE" ]; then
    error_exit "Fichier de sauvegarde non trouvé: $BACKUP_FILE"
fi

log "🔄 Début du rollback avec $1"

# Arrêt des services
log "⏹️ Arrêt des services..."
docker-compose down

# Sauvegarde de l'état actuel
log "💾 Sauvegarde de l'état actuel..."
CURRENT_BACKUP="$BACKUP_DIR/pre-rollback-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "$CURRENT_BACKUP" uploads/ server/.env 2>/dev/null || true

# Restauration
log "📦 Restauration des données..."
tar -xzf "$BACKUP_FILE" || error_exit "Échec de la restauration"

# Redémarrage
log "🚀 Redémarrage des services..."
docker-compose up -d || error_exit "Échec du redémarrage"

# Vérification
log "🏥 Vérification des services..."
sleep 10

for i in {1..30}; do
    if curl -f http://localhost:3000/health >/dev/null 2>&1; then
        log "✅ Rollback terminé avec succès"
        break
    fi
    
    if [ $i -eq 30 ]; then
        error_exit "Les services ne répondent pas après le rollback"
    fi
    
    sleep 10
done

log "🎉 Rollback terminé avec succès!"
