FROM golang:1.25-alpine AS builder

WORKDIR /src
RUN apk add --no-cache git ca-certificates

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /out/leads ./cmd/leads

FROM alpine:3.21

RUN adduser -D -u 1000 appuser
WORKDIR /app

COPY --from=builder /out/leads /app/leads
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

USER appuser
EXPOSE 8003

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["web"]
