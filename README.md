# POC Lead Management Apps

Proof-of-Concept web apps (Spring Boot, Pyramid, Django, Go). Each includes Bootstrap 5 CRUD for leads, a background welcome-email simulation, and scheduled health/dummy jobs.

Welcome emails are **simulated** (logged only; no SMTP).

| App | Directory | Port |
|-----|-----------|------|
| Spring Boot | `springboot-app/` | http://localhost:8001 |
| Pyramid | `pyramid-app/` | http://localhost:6543 |
| Django | `django-app/` | http://localhost:8000 |
| Go | `go-app/` | http://localhost:8003 |

## Prerequisites

Install [mise](https://mise.jdx.dev/), then from this directory:

```bash
mise install
mise exec -- java -version
mise exec -- mvn -version
mise exec -- python --version   # Python 3.12 for this repo
```

## 1. Spring Boot

```bash
cd springboot-app
mkdir -p data
mise exec -- mvn spring-boot:run
```

- Open http://localhost:8001
- JPA creates tables on startup (`ddl-auto=update`)
- `@Async` welcome email runs on lead create
- `@Scheduled(fixedRate = 1800000)` health check writes to `audit_log`

## 2. Pyramid

Pyramid uses **two processes** (same shape as Django): web + worker, sharing a SQLite job queue.

```bash
cd pyramid-app
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
mkdir -p data
python -c "from leads_app.models import init_db; init_db('sqlite:///./data/leads.db')"
```

Two terminals:

```bash
SQLALCHEMY_URL=sqlite:///./data/leads.db pserve development.ini
SQLALCHEMY_URL=sqlite:///./data/leads.db SCHEDULER_JOBSTORE_URL=sqlite:///./data/apscheduler.db pyramid-worker
```

- Open http://localhost:6543
- Lead create writes a `background_jobs` row (SQLite queue)
- `pyramid-worker` polls the queue for mock welcome emails and runs APScheduler every 30 minutes

## 3. Django

Django uses **MySQL** (via PyMySQL). Defaults match Docker Compose:

| Variable | Default |
|----------|---------|
| `DB_HOST` | `host.docker.internal` |
| `DB_PORT` | `3306` |
| `DB_USERNAME` | `root` |
| `DB_PASSWORD` | `password` |
| `DB_NAME` | `django_leads` |

```bash
cd django-app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DB_HOST=127.0.0.1 DB_PORT=3306 DB_USERNAME=root DB_PASSWORD=password DB_NAME=django_leads
python manage.py migrate
```

Run the web server and Django-Q cluster (two terminals):

```bash
# Local dev
python manage.py runserver 8000
python manage.py qcluster

# Or mirror Docker (1 worker, 2 threads):
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 1 --threads 2
```

- Open http://localhost:8000
- Lead create enqueues `send_welcome_email` via Django-Q (`Q_CLUSTER` uses 1 worker)
- A Django-Q schedule runs `leads.tasks.run_health_check` every 30 minutes
- You can also run the health check manually: `python manage.py health_check`
- Docker image is multi-stage slim with `PYTHONOPTIMIZE=1` and gunicorn
- Containers call `CREATE DATABASE IF NOT EXISTS` on startup, then migrate

## 4. Go

Go uses the **same shared MySQL** as Django (`DB_*` env vars). Defaults:

| Variable | Default |
|----------|---------|
| `DB_HOST` | `host.docker.internal` |
| `DB_PORT` | `3306` |
| `DB_USERNAME` | `root` |
| `DB_PASSWORD` | `password` |
| `DB_NAME` | `go_leads` |

```bash
cd go-app
mise exec -- go run ./cmd/leads web      # http://localhost:8003
mise exec -- go run ./cmd/leads worker   # queue + schedules
```

- Lead create enqueues a `welcome_email` row in `background_jobs`
- Worker drains the queue and runs `health_check` + `dummy_job` every 1s
- Startup ensures the MySQL database exists, then creates tables

## Deploy with Docker Compose

Each app has its own `Dockerfile` and `docker-compose.yml`. Ports do not overlap, so all can run on one host.

| App | Compose directory | Host port | URL |
|-----|-------------------|-----------|-----|
| Spring Boot | `springboot-app/` | **8001** | http://localhost:8001 |
| Pyramid | `pyramid-app/` | **6543** | http://localhost:6543 (web + worker) |
| Django | `django-app/` | **8000** | http://localhost:8000 (web + qcluster) |
| Go | `go-app/` | **8003** | http://localhost:8003 (web + worker) |

Pyramid, Django, and Go run **two containers** (web + background worker) for a fair resource comparison. Welcome email is **mocked** everywhere (`[MOCK MAIL]` logs only — no SMTP).

```bash
# Spring Boot (port 8001) — single container
cd springboot-app && docker compose up -d --build

# Pyramid (port 6543) — pyramid-web + pyramid-worker
cd ../pyramid-app && docker compose up -d --build

# Django (port 8000) — django-web + django-qcluster
cd ../django-app && docker compose up -d --build

# Go (port 8003) — go-web + go-worker
cd ../go-app && docker compose up -d --build
```

Useful commands (from each app directory):

```bash
docker compose logs -f
docker compose down
```

SQLite data for Spring Boot / Pyramid is in named volumes (`springboot-data`, `pyramid-data`). Django and Go use the shared external MySQL (`DB_*` env vars; see each app’s `.env.example`).

## Notes

- Spring Boot / Pyramid SQLite files live under each app’s `data/` directory (or Docker volume).
- Django / Go expect a reachable MySQL/MariaDB; override `DB_HOST` if the DB is another Compose service (e.g. `gemtech_mariadb_dev` network alias).
- Use `mise exec -- <command>` if tools are not on your PATH after `mise install`.
- Mail is mocked everywhere (`MockMailClient` / Django `locmem` backend) — safe for server demos.
