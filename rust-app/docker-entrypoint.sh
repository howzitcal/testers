#!/bin/sh
set -e

case "$1" in
  web)
    exec /app/leads web
    ;;
  worker)
    exec /app/leads worker
    ;;
  *)
    exec "$@"
    ;;
esac
