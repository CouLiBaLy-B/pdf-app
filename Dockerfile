# Dockerfile pour containeriser l'application (pour développement)
FROM python:3.13-slim

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

# Créer le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Exposer le port pour X11 forwarding (si nécessaire)
ENV DISPLAY=:0

# Commande par défaut
CMD ["python", "main.py"]