FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data \
    && groupadd -r kellerlog && useradd -r -g kellerlog -u 1000 kellerlog \
    && chown -R kellerlog:kellerlog /app

USER kellerlog

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

LABEL org.opencontainers.image.source=https://github.com/KrapfalAT/kellerlog
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
