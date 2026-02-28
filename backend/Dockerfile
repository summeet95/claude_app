FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run migrations then start server
CMD ["sh", "-c", \
     "alembic upgrade head && \
      python -m app.db.seeds.hairstyle_seed && \
      uvicorn app.main:app --host 0.0.0.0 --port 8000"]
