#!/bin/bash

# Script de restauration pour PDF Editor
set -e

BACKUP_DIR="/backups/pdf-editor"
S3_BUCKET="${S3_BUCKET:-pdf-editor-backups}"
LOG_FILE="/var/log/pdf-editor-restore.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

list_backups() {
    log "📋 Sauvegardes disponibles:"
    
    echo "=== SAUVEGARDES LOCALES ==="
    find "$BACKUP_DIR" -name "pdf-editor-backup-*.tar.gz" -printf "%T@ %Tc %p\n" 2>/dev/null | \
        sort -nr | head -10 | while read -r timestamp date time timezone file; do
        local size=$(stat -c%s "$file" 2>/dev/null || echo 0)
        local size_mb=$(( size / 1048576 ))
        echo "$(basename "$file") - $date $time (${size_mb}MB)"
    done
    
    if [ -n "$S3_BUCKET" ] && command -v aws >/dev/null 2>&1; then
        echo ""
        echo "=== SAUVEGARDES S3 ==="
        aws s3 ls "s3://$S3_BUCKET/backups/" --human-readable 2>/dev/null | \
            grep "pdf-editor-backup-" | tail -10
    fi
}

download_from_s3() {
    local backup_name=$1
    local local_path="$BACKUP_DIR/$backup_name"
    
    if [ -f "$local_path" ]; then
        log "✅ Sauvegarde déjà disponible localement"
        echo "$local_path"
        return 0
    fi
    
    if [ -z "$S3_BUCKET" ] || ! command -v aws >/dev/null 2>&1; then
        log "❌ S3 non configuré ou AWS CLI non disponible"
        return 1
    fi
    
    log "⬇️ Téléchargement depuis S3..."
    
    if aws s3 cp "s3://$S3_BUCKET/backups/$backup_name" "$local_path"; then
        log "✅ Téléchargement réussi"
        echo "$local_path"
        return 0
    else
        log "❌ Échec du téléchargement"
        return 1
    fi
}

stop_services() {
    log "⏹️ Arrêt des services..."
    
    cd /opt/pdf-editor
    docker-compose -f docker-compose.prod.yml down
    
    log "✅ Services arrêtés"
}

restore_backup() {
    local backup_file=$1
    
    log "🔄 Restauration de la sauvegarde: $(basename "$backup_file")"
    
    # Vérifier l'intégrité de l'archive
    if ! tar -tzf "$backup_file" >/dev/null 2>&1; then
        log "❌ Archive corrompue"
        return 1
    fi
    
    # Créer un répertoire temporaire
    local temp_dir=$(mktemp -d)
    
    # Extraire l'archive
    log "📦 Extraction de l'archive..."
    tar -xzf "$backup_file" -C "$temp_dir"
    
    local backup_content="$temp_dir/$(basename "$backup_file" .tar.gz)"
    
    # Restaurer les volumes Docker
    log "🔄 Restauration des volumes Docker..."
    
    # Volume uploads
    if [ -f "$backup_content/uploads.tar.gz" ]; then
        docker run --rm \
            -v pdf-editor_uploads_data:/data \
            -v "$backup_content:/backup" \
            alpine sh -c "rm -rf /data/* && tar -xzf /backup/uploads.tar.gz -C /data"
        log "✅ Volume uploads restauré"
    fi
    
    # Volume logs
    if [ -f "$backup_content/logs.tar.gz" ]; then
        docker run --rm \
            -v pdf-editor_logs_data:/data \
            -v "$backup_content:/backup" \
            alpine sh -c "rm -rf /data/* && tar -xzf /backup/logs.tar.gz -C /data"
        log "✅ Volume logs restauré"
    fi
    
    # Volume Redis
    if [ -f "$backup_content/redis.tar.gz" ]; then
        docker run --rm \
            -v pdf-editor_redis_data:/data \
            -v "$backup_content:/backup" \
            alpine sh -c "rm -rf /data/* && tar -xzf /backup/redis.tar.gz -C /data"
        log "✅ Volume Redis restauré"
    fi
    
    # Restaurer la configuration
    log "⚙️ Restauration de la configuration..."
    
    if [ -f "$backup_content/docker-compose.prod.yml" ]; then
        cp "$backup_content/docker-compose.prod.yml" /opt/pdf-editor/
    fi
    
    if [ -f "$backup_content/.env" ]; then
        cp "$backup_content/.env" /opt/pdf-editor/
    fi
    
    if [ -d "$backup_content/nginx" ]; then
        cp -r "$backup_content/nginx" /opt/pdf-editor/
    fi
    
    # Nettoyage
    rm -rf "$temp_dir"
    
    log "✅ Restauration terminée"
}

start_services() {
    log "▶️ Démarrage des services..."
    
    cd /opt/pdf-editor
    docker-compose -f docker-compose.prod.yml up -d
    
    # Attendre que les services démarrent
    sleep 30
    
    # Vérifier la santé
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:3000/health >/dev/null 2>&1; then
            log "✅ Services démarrés et fonctionnels"
            return 0
        fi
        
        sleep 10
        ((attempt++))
    done
    
    log "❌ Les services ne répondent pas"
    return 1
}

main() {
    local backup_name=$1
    
    if [ -z "$backup_name" ]; then
        echo "Usage: $0 <nom-de-sauvegarde>"
        echo ""
        list_backups
        exit 1
    fi
    
    log "🚀 Début de la restauration: $backup_name"
    
    # Confirmation
    echo "⚠️ ATTENTION: Cette opération va:"
    echo "  - Arrêter tous les services PDF Editor"
    echo "  - Remplacer toutes les données actuelles"
    echo "  - Restaurer la sauvegarde: $backup_name"
    echo ""
    read -p "Êtes-vous sûr de vouloir continuer? (oui/non): " confirm
    
    if [ "$confirm" != "oui" ]; then
        log "❌ Restauration annulée"
        exit 1
    fi
    
    # Télécharger la sauvegarde si nécessaire
    local backup_file="$BACKUP_DIR/$backup_name"
    
    if [ ! -f "$backup_file" ]; then
        if backup_file=$(download_from_s3 "$backup_name"); then
            log "✅ Sauvegarde téléchargée"
        else
            log "❌ Impossible de trouver la sauvegarde"
            exit 1
        fi
    fi
    
    # Créer une sauvegarde de sécurité avant restauration
    log "💾 Création d'une sauvegarde de sécurité..."
    /opt/pdf-editor/scripts/backup.sh || log "⚠️ Échec de la sauvegarde de sécurité"
    
    # Arrêter les services
    stop_services
    
    # Restaurer
    if restore_backup "$backup_file"; then
        log "✅ Restauration réussie"
    else
        log "❌ Échec de la restauration"
        exit 1
    fi
    
    # Redémarrer les services
    if start_services; then
        log "✅ Services redémarrés"
    else
        log "❌ Échec du redémarrage des services"
        exit 1
    fi
    
    log "🎉 Restauration terminée avec succès"
    
    # Notification
    if command -v mail >/dev/null 2>&1; then
                echo "Restauration PDF Editor réussie: $backup_name" | \
            mail -s "PDF Editor - Restauration réussie" admin@yourdomain.com 2>/dev/null || true
    fi
}

# Exécuter la restauration
main "$@"
