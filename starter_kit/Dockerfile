FROM python:3.11-slim
WORKDIR /app

# system deps for psycopg2 if later needed
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app

EXPOSE 8080
CMD ["gunicorn","-k","uvicorn.workers.UvicornWorker","main:app","-b","0.0.0.0:8080","--workers","1","--threads","4"]
