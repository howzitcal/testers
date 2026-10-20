#!/bin/sh
set -e

case "$1" in
  web)
    exec bun run main.js web
    ;;
  worker)
    exec bun run main.js worker
    ;;
  *)
    exec "$@"
    ;;
esac
