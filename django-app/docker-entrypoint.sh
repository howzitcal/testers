#!/bin/sh
set -e

# Ensure MySQL database exists, then migrate
python - <<'PY'
import os
import sys
import time

import pymysql

host = os.environ.get("DB_HOST", "host.docker.internal")
port = int(os.environ.get("DB_PORT", "3306"))
user = os.environ.get("DB_USERNAME", "root")
password = os.environ.get("DB_PASSWORD", "password")
db_name = os.environ.get("DB_NAME", "django_leads")

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
