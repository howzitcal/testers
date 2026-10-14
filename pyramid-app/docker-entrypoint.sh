#!/bin/sh
set -e

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
