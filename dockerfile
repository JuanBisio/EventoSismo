# Dockerfile

# 1. Partimos de una imagen ligera de Python 3.9
FROM python:3.9-slim

# 2. Configuramos el directorio de trabajo dentro del contenedor
WORKDIR /usr/src/app

# 3. Copiamos los archivos de tu proyecto dentro del contenedor
COPY . .

# 4. Instalamos pip, actualizamos y luego instalamos las dependencias
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 5. Exponemos el puerto 8000 (este será el puerto que Gunicorn atenderá)
EXPOSE 8000

# 6. Definimos el comando por defecto que iniciará Gunicorn
#    “app_flask:app” indica “archivo app_flask.py, variable Flask llamada 'app'”
CMD ["gunicorn", "app_flask:app", "--bind", "0.0.0.0:8000"]
