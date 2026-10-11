#!/bin/sh
set -e

mkdir -p /app/data

case "$1" in
  web)
    exec pserve production.ini
    ;;
  worker)
    exec pyramid-worker
    ;;
  *)
    exec "$@"
    ;;
esac
