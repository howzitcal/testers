#!/bin/sh
set -e

mkdir -p /app/data
python manage.py migrate --noinput

case "$1" in
  web)
    exec gunicorn config.wsgi:application \
      --bind 0.0.0.0:8000 \
      --workers 1 \
      --threads 2 \
      --timeout 60 \
      --access-logfile - \
      --error-logfile -
    ;;
  qcluster)
    exec python manage.py qcluster
    ;;
  *)
    exec "$@"
    ;;
esac
