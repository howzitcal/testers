FROM node:24-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY main.js ./
COPY src ./src
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh \
    && adduser -D -u 1000 appuser \
    && chown -R appuser:appuser /app

USER appuser
EXPOSE 8007

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["web"]
