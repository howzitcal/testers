#!/bin/sh
set -e

case "$1" in
  web)
    exec deno run -A main.ts web
    ;;
  worker)
    exec deno run -A main.ts worker
    ;;
  *)
    exec "$@"
    ;;
esac
