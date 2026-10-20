FROM oven/bun:1.4.2-alpine

WORKDIR /app

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY main.js ./
COPY src ./src
COPY docker-entrypoint.sh /docker-entrypoint.sh

USER root
RUN chmod +x /docker-entrypoint.sh \
    && chown -R bun:bun /app
USER bun

EXPOSE 8005

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["web"]
