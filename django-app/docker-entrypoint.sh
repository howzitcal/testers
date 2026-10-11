#!/bin/sh
set -e

mkdir -p /app/data
python manage.py migrate --noinput

case "$1" in
  web)
    exec python manage.py runserver 0.0.0.0:8000
    ;;
  qcluster)
    exec python manage.py qcluster
    ;;
  *)
    exec "$@"
    ;;
esac
