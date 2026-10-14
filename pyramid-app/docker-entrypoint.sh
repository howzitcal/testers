#!/bin/sh
set -e

# Ensure shared MySQL database exists (same pattern as django-app)
python - <<'PY'
import os
import sys
import time

import pymysql

host = os.environ.get("DB_HOST", "host.docker.internal")
port = int(os.environ.get("DB_PORT", "3306"))
user = os.environ.get("DB_USERNAME", "root")
password = os.environ.get("DB_PASSWORD", "password")
db_name = os.environ.get("DB_NAME", "pyramid_leads")

for attempt in range(1, 31):
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=password)
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.close()
        print(f"MySQL ready; database `{db_name}` ensured")
        break
    except Exception as exc:
        print(f"Waiting for MySQL ({attempt}/30): {exc}", flush=True)
        time.sleep(2)
else:
    print("Could not connect to MySQL", file=sys.stderr)
    sys.exit(1)
PY

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
