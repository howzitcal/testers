FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY manage.py .
COPY config ./config
COPY leads ./leads
COPY templates ./templates
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh \
    && mkdir -p /app/data

EXPOSE 8000
VOLUME ["/app/data"]

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["web"]
