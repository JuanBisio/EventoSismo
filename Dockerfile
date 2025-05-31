# Dockerfile (en la raíz de “PPAI/”)
FROM python:3.9-slim

# 1) Directorio de trabajo dentro del contenedor
WORKDIR /usr/src/app

# 2) Copiamos todos los archivos de la app
COPY . .

# 3) Instalamos pip y las dependencias
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 4) Exponemos un “placeholder” de puerto (Vercel instala su propio $PORT)
EXPOSE 8000

# 5) Comando para iniciar Gunicorn en el puerto que Vercel asigne
CMD ["sh", "-c", "gunicorn app_flask:app --bind 0.0.0.0:$PORT"]
