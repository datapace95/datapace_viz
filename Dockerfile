# Utiliser une image de base Python
FROM python:3.11.5

# Exposer le port utilisé par Streamlit
EXPOSE 8501

# Définir le répertoire de travail
WORKDIR /app

# Copy only requirements first to leverage Docker caching
COPY requirements.txt ./

# Install dependencies with no cache to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . ./

# Définir la commande de démarrage
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]