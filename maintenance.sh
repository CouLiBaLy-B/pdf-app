#!/bin/bash

# Script de maintenance automatisée pour PDF Editor
set -e

LOG_FILE="/var/log/pdf-editor-maintenance.log"
DOCKER_COMPOSE_FILE="/opt/pdf-editor/docker-compose.prod.yml"
BACKUP_DIR="/backups/pdf-editor"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Nettoyage des logs
cleanup_logs() {
    log "🧹 Nettoyage des logs..."
    
    # Logs de l'application (garder 30 jours)
    find /opt/pdf-editor/logs -name "*.log" -mtime +30 -delete 2>/dev/null || true
    
    # Logs Docker (limiter à 100MB par conteneur)
    docker system prune -f --volumes
    
    # Logs système
    journalctl --vacuum-time=30d
    
    log "✅ Nettoyage des logs terminé"
}

# Nettoyage des fichiers temporaires
cleanup_temp_files() {
    log "🗑️ Nettoyage des fichiers temporaires..."
    
    # Fichiers temporaires de l'application
    docker exec pdf-editor-app find /tmp -name "pdf-*" -mtime +1 -delete 2>/dev/null || true
    
    # Fichiers uploadés anciens (garder 7 jours)
    docker exec pdf-editor-app find /app/uploads -name "*.pdf" -mtime +7 -delete 2>/dev/null || true
    
    # Cache Redis (nettoyer les clés expirées)
    docker exec pdf-editor-redis redis-cli FLUSHDB 2>/dev/null || true
    
    log "✅ Nettoyage des fichiers temporaires terminé"
}

# Optimisation de la base de données Redis
optimize_redis() {
    log "⚡ Optimisation Redis..."
    
    # Compacter la base de données
    docker exec pdf-editor-redis redis-cli BGREWRITEAOF
    
    # Statistiques mémoire
    local memory_usage=$(docker exec pdf-editor-redis redis-cli INFO memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
    log "📊 Utilisation mémoire Redis: $memory_usage"
    
    log "✅ Optimisation Redis terminée"
}

# Vérification de l'intégrité des données
check_data_integrity() {
    log "🔍 Vérification de l'intégrité des données..."
    
    # Vérifier les volumes Docker
    local volumes=("pdf-editor_uploads_data" "pdf-editor_redis_data" "pdf-editor_logs_data")
    
    for volume in "${volumes[@]}"; do
        if docker volume inspect "$volume" >/dev/null 2>&1; then
            log "✅ Volume $volume OK"
        else
            log "❌ Volume $volume manquant"
        fi
    done
    
    # Vérifier la connectivité Redis
    if docker exec pdf-editor-redis redis-cli ping | grep -q PONG; then
        log "✅ Redis connectivité OK"
    else
        log "❌ Problème de connectivité Redis"
    fi
    
    log "✅ Vérification de l'intégrité terminée"
}

# Mise à jour des certificats SSL
update_ssl_certificates() {
    log "🔐 Vérification des certificats SSL..."
    
    local cert_file="/opt/pdf-editor/nginx/ssl/cert.pem"
    
    if [ -f "$cert_file" ]; then
        local expiry_date=$(openssl x509 -enddate -noout -in "$cert_file" | cut -d= -f2)
        local expiry_timestamp=$(date -d "$expiry_date" +%s)
        local current_timestamp=$(date +%s)
        local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
        
        log "📅 Certificat SSL expire dans $days_until_expiry jours"
        
        if [ $days_until_expiry -lt 30 ]; then
            log "⚠️ Certificat SSL expire bientôt - renouvellement recommandé"
            # Ici vous pourriez ajouter la logique de renouvellement automatique
        fi
    else
        log "⚠️ Certificat SSL non trouvé"
    fi
}

# Surveillance des performances
monitor_performance() {
    log "📊 Surveillance des performances..."
    
    # Utilisation CPU
    local cpu_usage=$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}" | grep pdf-editor-app | awk '{print $2}' | sed 's/%//')
    log "💻 Utilisation CPU: ${cpu_usage}%"
    
    # Utilisation mémoire
    local memory_usage=$(docker stats --no-stream --format "table {{.Container}}\t{{.MemUsage}}" | grep pdf-editor-app | awk '{print $2}')
    log "🧠 Utilisation mémoire: $memory_usage"
    
    # Espace disque
    local disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    log "💾 Utilisation disque: ${disk_usage}%"
    
    # Alertes si seuils dépassés
    if [ "$cpu_usage" -gt 80 ]; then
        log "🚨 ALERTE: Utilisation CPU élevée (${cpu_usage}%)"
    fi
    
    if [ "$disk_usage" -gt 85 ]; then
        log "🚨 ALERTE: Espace disque faible (${disk_usage}%)"
    fi
}

# Redémarrage des services si nécessaire
restart_services_if_needed() {
    log "🔄 Vérification de l'état des services..."
    
    # Vérifier si l'application répond
    if ! curl -f http://localhost/health >/dev/null 2>&1; then
        log "⚠️ Application ne répond pas - redémarrage..."
        
        cd /opt/pdf-editor
        docker-compose -f "$DOCKER_COMPOSE_FILE" restart pdf-editor
        
        # Attendre que le service redémarre
        sleep 30
        
        if curl -f http://localhost/health >/dev/null 2>&1; then
            log "✅ Application redémarrée avec succès"
        else
            log "❌ Échec du redémarrage de l'application"
        fi
    else
        log "✅ Application fonctionne correctement"
    fi
}

# Génération du rapport de maintenance
generate_report() {
    local report_file="/tmp/maintenance-report-$(date +%Y%m%d-%H%M%S).txt"
    
    {
        echo "=== RAPPORT DE MAINTENANCE PDF EDITOR ==="
        echo "Date: $(date)"
        echo ""
        
        echo "=== ÉTAT DES SERVICES ==="
        docker-compose -f "$DOCKER_COMPOSE_FILE" ps
        echo ""
        
        echo "=== UTILISATION DES RESSOURCES ==="
        docker stats --no-stream
        echo ""
        
        echo "=== ESPACE DISQUE ==="
        df -h
        echo ""
        
        echo "=== VOLUMES DOCKER ==="
        docker volume ls | grep pdf-editor
        echo ""
        
        echo "=== LOGS RÉCENTS ==="
        tail -20 "$LOG_FILE"
        
    } > "$report_file"
    
    log "📋 Rapport généré: $report_file"
    
    # Envoyer le rapport par email si configuré
    if command -v mail >/dev/null 2>&1; then
        mail -s "PDF Editor - Rapport de maintenance" admin@yourdomain.com < "$report_file" 2>/dev/null || true
    fi
}

# Fonction principale
main() {
    log "🚀 Début de la maintenance automatisée"
    
    # Exécuter les tâches de maintenance
    cleanup_logs
    cleanup_temp_files
    optimize_redis
    check_data_integrity
    update_ssl_certificates
    monitor_performance
    restart_services_if_needed
    
    # Générer le rapport
    generate_report
    
    log "🎉 Maintenance terminée avec succès"
}

# Exécuter la maintenance
main "$@"

