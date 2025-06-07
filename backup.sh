#!/bin/bash

# Script de sauvegarde automatisée pour PDF Editor
set -e

BACKUP_DIR="/backups/pdf-editor"
S3_BUCKET="${S3_BUCKET:-pdf-editor-backups}"
RETENTION_DAYS=30
LOG_FILE="/var/log/pdf-editor-backup.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

create_backup() {
    local timestamp=$(date +%Y%m%d-%H%M%S)
    local backup_name="pdf-editor-backup-$timestamp"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    log "💾 Création de la sauvegarde: $backup_name"
    
    mkdir -p "$backup_path"
    
    # Sauvegarder les volumes Docker
    log "📦 Sauvegarde des volumes Docker..."
    
    # Volume uploads
    docker run --rm \
        -v pdf-editor_uploads_data:/data:ro \
        -v "$backup_path:/backup" \
        alpine tar -czf /backup/uploads.tar.gz -C /data . 2>/dev/null || true
    
    # Volume logs
    docker run --rm \
        -v pdf-editor_logs_data:/data:ro \
        -v "$backup_path:/backup" \
        alpine tar -czf /backup/logs.tar.gz -C /data . 2>/dev/null || true
    
    # Volume Redis
    docker run --rm \
        -v pdf-editor_redis_data:/data:ro \
        -v "$backup_path:/backup" \
        alpine tar -czf /backup/redis.tar.gz -C /data . 2>/dev/null || true
    
    # Sauvegarder la configuration
    log "⚙️ Sauvegarde de la configuration..."
    cp -r /opt/pdf-editor/*.yml "$backup_path/" 2>/dev/null || true
    cp -r /opt/pdf-editor/.env "$backup_path/" 2>/dev/null || true
    cp -r /opt/pdf-editor/nginx "$backup_path/" 2>/dev/null || true
    
    # Créer l'archive finale
    log "🗜️ Compression de la sauvegarde..."
    tar -czf "$backup_path.tar.gz" -C "$BACKUP_DIR" "$backup_name"
    rm -rf "$backup_path"
    
    log "✅ Sauvegarde créée: $backup_path.tar.gz"
    echo "$backup_path.tar.gz"
}

upload_to_s3() {
    local backup_file=$1
    
    if [ -z "$S3_BUCKET" ] || ! command -v aws >/dev/null 2>&1; then
        log "⚠️ S3 non configuré ou AWS CLI non disponible"
        return 0
    fi
    
    log "☁️ Upload vers S3: $S3_BUCKET"
    
    local s3_key="backups/$(basename "$backup_file")"
    
    if aws s3 cp "$backup_file" "s3://$S3_BUCKET/$s3_key"; then
        log "✅ Upload S3 réussi: s3://$S3_BUCKET/$s3_key"
        
        # Configurer la politique de cycle de vie S3 si nécessaire
        aws s3api put-object-tagging \
            --bucket "$S3_BUCKET" \
            --key "$s3_key" \
            --tagging "TagSet=[{Key=AutoDelete,Value=true},{Key=RetentionDays,Value=$RETENTION_DAYS}]" \
            2>/dev/null || true
    else
        log "❌ Échec de l'upload S3"
        return 1
    fi
}

cleanup_old_backups() {
    log "🧹 Nettoyage des anciennes sauvegardes..."
    
    # Nettoyage local
    find "$BACKUP_DIR" -name "pdf-editor-backup-*.tar.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    
    # Nettoyage S3
    if [ -n "$S3_BUCKET" ] && command -v aws >/dev/null 2>&1; then
        local cutoff_date=$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d)
        
        aws s3api list-objects-v2 \
            --bucket "$S3_BUCKET" \
            --prefix "backups/" \
            --query "Contents[?LastModified<='$cutoff_date'].Key" \
            --output text | \
        while read -r key; do
            if [ -n "$key" ]; then
                aws s3 rm "s3://$S3_BUCKET/$key"
                log "🗑️ Supprimé de S3: $key"
            fi
        done
    fi
    
    log "✅ Nettoyage terminé"
}

verify_backup() {
    local backup_file=$1
    
    log "🔍 Vérification de la sauvegarde..."
    
    # Vérifier l'intégrité de l'archive
    if tar -tzf "$backup_file" >/dev/null 2>&1; then
        log "✅ Archive valide"
    else
        log "❌ Archive corrompue"
        return 1
    fi
    
    # Vérifier la taille minimale (au moins 1MB)
    local size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file" 2>/dev/null || echo 0)
    if [ "$size" -gt 1048576 ]; then
        log "✅ Taille de sauvegarde acceptable: $(( size / 1048576 ))MB"
    else
        log "❌ Sauvegarde trop petite: ${size} bytes"
        return 1
    fi
    
    return 0
}

send_notification() {
    local status=$1
    local message=$2
    
    # Notification par email
    if command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "PDF Editor Backup - $status" admin@yourdomain.com 2>/dev/null || true
    fi
    
    # Notification Slack
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        local color="good"
        [ "$status" = "ERROR" ] && color="danger"
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"title\":\"PDF Editor Backup\",\"text\":\"$message\"}]}" \
            "$SLACK_WEBHOOK_URL" 2>/dev/null || true
    fi
}

main() {
    log "🚀 Début de la sauvegarde PDF Editor"
    
    mkdir -p "$BACKUP_DIR"
    
    # Créer la sauvegarde
    local backup_file
    if backup_file=$(create_backup); then
        log "✅ Sauvegarde créée avec succès"
    else
        log "❌ Échec de la création de sauvegarde"
        send_notification "ERROR" "Échec de la création de sauvegarde PDF Editor"
        exit 1
    fi
    
    # Vérifier la sauvegarde
    if verify_backup "$backup_file"; then
        log "✅ Sauvegarde vérifiée"
    else
        log "❌ Vérification de sauvegarde échouée"
        send_notification "ERROR" "Sauvegarde PDF Editor corrompue: $backup_file"
        exit 1
    fi
    
    # Upload vers S3
    if upload_to_s3 "$backup_file"; then
        log "✅ Upload réussi"
    else
        log "⚠️ Upload échoué mais sauvegarde locale disponible"
    fi
    
    # Nettoyage
    cleanup_old_backups
    
    local backup_size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file" 2>/dev/null || echo 0)
    local backup_size_mb=$(( backup_size / 1048576 ))
    
    log "🎉 Sauvegarde terminée avec succès"
    send_notification "SUCCESS" "Sauvegarde PDF Editor réussie: $(basename "$backup_file") (${backup_size_mb}MB)"
}

# Exécuter la sauvegarde
main "$@"

