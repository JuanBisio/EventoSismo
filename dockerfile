# Dockerfile corregido: escucha en $PORT en lugar de puerto fijo

FROM python:3.9-slim

# 1) Directorio de trabajo
WORKDIR /usr/src/app

# 2) Copiar todos los archivos del proyecto
COPY . .

# 3) Instalar dependencias
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 4) Exponer (sin número fijo; Vercel usará su propia variable $PORT, pero mantenemos esta línea para documentación interna)
EXPOSE 8000

# 5) CMD en formato “exec”: Gunicorn lee la variable de entorno $PORT
#    Usamos “sh -c” para que $PORT se expanda dinámicamente al iniciar el contenedor.
CMD ["sh", "-c", "gunicorn app_flask:app --bind 0.0.0.0:$PORT"]
