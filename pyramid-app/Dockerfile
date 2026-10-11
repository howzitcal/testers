FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt setup.py MANIFEST.in ./
COPY leads_app ./leads_app
COPY production.ini docker-entrypoint.sh ./

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -e . \
    && chmod +x /app/docker-entrypoint.sh \
    && mkdir -p /app/data

EXPOSE 6543
VOLUME ["/app/data"]

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["web"]
