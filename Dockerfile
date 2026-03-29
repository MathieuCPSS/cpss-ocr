# Image de base légère avec Python 3.10
FROM python:3.10-slim

# Dépendances système nécessaires pour PaddleOCR
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1 \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY app.py .

# Port exposé
EXPOSE 8080

# Démarrer le serveur
CMD ["python", "app.py"]
