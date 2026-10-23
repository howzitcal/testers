FROM openresty/openresty:10.0.2.1-0-jammy

RUN apt-get update && apt-get install -y --no-install-recommends \
      luarocks \
      libssl-dev \
      gcc \
      make \
      git \
      unzip \
      curl \
      default-mysql-client \
    && luarocks install --lua-version=5.1 lapis \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY config.lua app.lua models.lua nginx.conf mime.types schema.sql worker.lua ./
COPY views ./views
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN mkdir -p logs \
    && chmod +x /docker-entrypoint.sh

ENV LAPIS_OPENRESTY=/usr/local/openresty/bin/openresty \
    PATH="/usr/local/openresty/bin:/usr/local/openresty/nginx/sbin:${PATH}" \
    HTTP_PORT=8009

EXPOSE 8009

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["web"]
