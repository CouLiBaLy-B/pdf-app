#!/bin/bash

# Configuration des tâches cron
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Créer le fichier crontab
cat > /tmp/pdf-editor-cron << EOF
# Sauvegarde quotidienne à 2h du matin
0 2 * * * $SCRIPT_DIR/backup.sh

# Nettoyage des logs hebdomadaire
0 3 * * 0 find /var/log -name "*pdf-editor*" -mtime +7 -delete

# Vérification de santé toutes les 5 minutes
*/5 * * * * curl -f http://localhost:3000/health || echo "Service down" | mail -s "PDF Editor Alert" admin@example.com

# Redémarrage automatique le dimanche à 4h (maintenance)
0 4 * * 0 $SCRIPT_DIR/restart.sh

# Mise à jour des certificats SSL (si Let's Encrypt)
0 1 1 * * certbot renew --quiet && docker-compose restart nginx

# Nettoyage Docker mensuel
0 5 1 * * docker system prune -f
EOF

# Installer le crontab
crontab /tmp/pdf-editor-cron
rm /tmp/pdf-editor-cron

echo "✅ Tâches cron configurées avec succès"
crontab -l
