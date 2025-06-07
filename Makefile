.PHONY: help install dev test build docker-build docker-run clean

# Variables
NODE_VERSION := 18
DOCKER_IMAGE := pdf-editor
DOCKER_TAG := latest

help: ## Affiche l'aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Installe les dépendances
	@echo "📦 Installation des dépendances..."
	cd server && npm install

dev: ## Démarre en mode développement
	@echo "🚀 Démarrage en mode développement..."
	cd server && npm run dev

test: ## Lance les tests
	@echo "🧪 Exécution des tests..."
	cd server && npm test

test-watch: ## Lance les tests en mode surveillance
	@echo "👀 Tests en mode surveillance..."
	cd server && npm run test:watch

lint: ## Vérifie le code avec ESLint
	@echo "🔍 Vérification du code..."
	cd server && npm run lint

build: ## Build pour la production
	@echo "🏗️ Build de production..."
	cd server && npm run build

docker-build: ## Construit l'image Docker
	@echo "🐳 Construction de l'image Docker..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-run: ## Lance le conteneur Docker
	@echo "🚀 Démarrage du conteneur..."
	docker-compose up -d

docker-stop: ## Arrête le conteneur Docker
	@echo "⏹️ Arrêt du conteneur..."
	docker-compose down

docker-logs: ## Affiche les logs du conteneur
	@echo "📋 Logs du conteneur..."
	docker-compose logs -f

clean: ## Nettoie les fichiers temporaires
	@echo "🧹 Nettoyage..."
	rm -rf server/node_modules
	rm -rf uploads/*
	rm -rf temp/*
	rm -rf logs/*
	docker system prune -f

deploy: test build docker-build ## Déploie l'application
	@echo "🚀 Déploiement..."
	docker-compose up -d --build

backup: ## Sauvegarde les données
	@echo "💾 Sauvegarde..."
	tar -czf backup-$(shell date +%Y%m%d-%H%M%S).tar.gz uploads/ server/.env

restore: ## Restaure depuis une sauvegarde
	@echo "🔄 Restauration..."
	@read -p "Nom du fichier de sauvegarde: " backup_file; \
	tar -xzf $$backup_file

security-audit: ## Audit de sécurité
	@echo "🔒 Audit de sécurité..."
	cd server && npm audit
	docker run --rm -v $(PWD):/app clair-scanner --ip $(shell docker network inspect bridge --format='{{range .IPAM.Config}}{{.Gateway}}{{end}}') $(DOCKER_IMAGE):$(DOCKER_TAG)

performance-test: ## Tests de performance
	@echo "⚡ Tests de performance..."
	cd server && npm run test:performance

docs: ## Génère la documentation
	@echo "📚 Génération de la documentation..."
	cd server && npm run docs

setup: install ## Configuration initiale complète
	@echo "⚙️ Configuration initiale..."
	cp .env.example server/.env
	mkdir -p uploads temp logs ssl
	@echo "✅ Configuration terminée. Modifiez server/.env selon vos besoins."

health-check: ## Vérifie l'état de l'application
	@echo "🏥 Vérification de l'état..."
	curl -f http://localhost:3000/health || echo "❌ Service non disponible"

monitor: ## Lance le monitoring
	@echo "📊 Démarrage du monitoring..."
	docker-compose -f docker-compose.monitoring.yml up -d

update: ## Met à jour les dépendances
	@echo "🔄 Mise à jour des dépendances..."
	cd server && npm update
	docker pull node:18-alpine
	docker pull nginx:alpine