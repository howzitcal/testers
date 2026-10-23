#!/bin/sh
set -e

case "$1" in
  web)
    exec node main.js web
    ;;
  worker)
    exec node main.js worker
    ;;
  *)
    exec "$@"
    ;;
esac
