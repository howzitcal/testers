#!/bin/sh
set -e

case "$1" in
  web)
    exec dotnet DotnetLeads.dll web
    ;;
  worker)
    exec dotnet DotnetLeads.dll worker
    ;;
  *)
    exec "$@"
    ;;
esac
