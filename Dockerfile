FROM node:18-alpine

# Créer le répertoire de l'application
WORKDIR /app

# Copier les fichiers package.json
COPY server/package*.json ./server/
COPY public/ ./public/

# Installer les dépendances
WORKDIR /app/server
RUN npm ci --only=production

# Copier le code source
COPY server/ .

# Créer un utilisateur non-root
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001

# Changer la propriété des fichiers
RUN chown -R nodejs:nodejs /app
USER nodejs

# Exposer le port
EXPOSE 3000

# Variables d'environnement
ENV NODE_ENV=production
ENV PORT=3000

# Commande de démarrage
CMD ["npm", "start"]