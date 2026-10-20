FROM denoland/deno:2.9.7

WORKDIR /app

COPY deno.json ./
COPY main.ts ./
COPY src ./src

RUN deno install --entrypoint main.ts

COPY docker-entrypoint.sh /docker-entrypoint.sh
USER root
RUN chmod +x /docker-entrypoint.sh \
    && chown -R deno:deno /app
USER deno

EXPOSE 8004

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["web"]
