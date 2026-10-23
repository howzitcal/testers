#!/bin/sh
set -e

DB_HOST="${DB_HOST:-host.docker.internal}"
DB_PORT="${DB_PORT:-3306}"
DB_USERNAME="${DB_USERNAME:-root}"
DB_PASSWORD="${DB_PASSWORD:-password}"
DB_NAME="${DB_NAME:-lapis_leads}"

echo "Waiting for MySQL at ${DB_HOST}:${DB_PORT}..."
i=1
while [ "$i" -le 30 ]; do
  if mysqladmin ping -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USERNAME" -p"$DB_PASSWORD" --silent 2>/dev/null; then
    break
  fi
  echo "Waiting for MySQL ($i/30)..."
  i=$((i + 1))
  sleep 2
done

mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USERNAME" -p"$DB_PASSWORD" -e \
  "CREATE DATABASE IF NOT EXISTS \`${DB_NAME}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
mysql -h"$DB_HOST" -P"$DB_PORT" -u"$DB_USERNAME" -p"$DB_PASSWORD" "$DB_NAME" < /app/schema.sql
echo "MySQL ready; database \`${DB_NAME}\` ensured"

cd /app
mkdir -p logs

case "$1" in
  web)
    exec lapis server production
    ;;
  worker)
    exec resty /app/worker.lua
    ;;
  *)
    exec "$@"
    ;;
esac
