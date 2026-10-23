FROM rust:1-bookworm AS builder

WORKDIR /src
COPY Cargo.toml ./
# Cache deps with a dummy main
RUN mkdir src && echo 'fn main(){}' > src/main.rs && cargo build --release && rm -rf src

COPY src ./src
RUN touch src/main.rs && cargo build --release

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 appuser

WORKDIR /app
COPY --from=builder /src/target/release/leads /app/leads
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh && chown -R appuser:appuser /app

USER appuser
EXPOSE 8006

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["web"]
