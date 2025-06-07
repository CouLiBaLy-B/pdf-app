# PDF Editor - Application de Production

## 🚀 Déploiement

### Prérequis
- Docker et Docker Compose
- Nginx
- Certificats SSL
- 4GB RAM minimum
- 20GB espace disque

### Installation rapide
```bash
git clone https://github.com/your-org/pdf-editor.git
cd pdf-editor
chmod +x scripts/*.sh
./scripts/deploy.sh
```

### Configuration
1. Modifier `.env` avec vos paramètres
2. Placer vos certificats SSL dans `nginx/ssl/`
3. Configurer les alertes dans `monitoring/alertmanager/config.yml`

## 📊 Monitoring

- **Grafana**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

## 🔧 Maintenance

### Sauvegardes automatiques
```bash
# Sauvegarde manuelle
./scripts/backup.sh

# Restauration
./scripts/restore.sh backup-name.tar.gz
```

### Maintenance
```bash
# Maintenance complète
./scripts/maintenance.sh

# Vérification de santé
curl http://localhost/health
```

## 🚨 Dépannage

### Logs
```bash
# Logs de l'application
docker logs pdf-editor-app

# Logs Nginx
docker logs pdf-editor-nginx

# Logs système
tail -f /var/log/pdf-editor-*.log
```

### Redémarrage des services
```bash
cd /opt/pdf-editor
docker-compose -f docker-compose.prod.yml restart
```

## 📈 Métriques

L'application expose des métriques Prometheus sur `/metrics`:
- Nombre de requêtes HTTP
- Temps de réponse
- Opérations PDF
- Utilisation mémoire
- Erreurs

## 🔒 Sécurité

- HTTPS obligatoire
- Rate limiting configuré
- Headers de sécurité
- Validation des fichiers
- Isolation des conteneurs

## 📞 Support

En cas de problème:
1. Vérifier les logs
2. Consulter Grafana pour les métriques
3. Exécuter les tests de santé
4. Contacter l'équipe technique

---

**Version**: 1.0.0  
**Dernière mise à jour**: $(date)
