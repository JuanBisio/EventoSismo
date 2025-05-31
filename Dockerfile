FROM python:3.9-slim

# 1) Directorio de trabajo dentro del contenedor
WORKDIR /usr/src/app

# 2) Copiamos todo el contenido del proyecto a /usr/src/app
COPY . .

# 3) Instalamos pip y las dependencias del requirements.txt
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 4) Exponemos un "puerto documental" (Vercel inyectará $PORT a runtime)
EXPOSE 8000

# 5) Arrancamos Gunicorn usando el objeto Flask “app” de app_flask.py
CMD ["sh", "-c", "gunicorn app_flask:app --bind 0.0.0.0:$PORT"]
