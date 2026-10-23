# POC Lead Management Apps

Proof-of-Concept web apps (Spring Boot, Pyramid, Django, Go, Deno, Bun, Rust, Node.js, .NET). Each includes Bootstrap 5 CRUD for leads, a background welcome-email simulation, and scheduled health/dummy jobs.

Welcome emails are **simulated** (logged only; no SMTP).

| App | Directory | Port |
|-----|-----------|------|
| Spring Boot | `springboot-app/` | http://localhost:8001 |
| Pyramid | `pyramid-app/` | http://localhost:6543 |
| Django | `django-app/` | http://localhost:8000 |
| Go | `go-app/` | http://localhost:8003 |
| Deno | `deno-app/` | http://localhost:8004 |
| Bun | `bun-app/` | http://localhost:8005 |
| Rust | `rust-app/` | http://localhost:8006 |
| Node.js | `node-app/` | http://localhost:8007 |
| .NET 10 | `dotnet-app/` | http://localhost:8008 |

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

### Django on PyPy (optional, parallel stack)

Same app, PyPy 3.12 image, separate compose file (CPython stack unchanged):

```bash
cd django-app
docker compose -f docker-compose.pypy.yml up -d --build
```

- http://localhost:8010
- Containers: `django-leads-pypy-web` + `django-leads-pypy-qcluster`
- DB default: `django_leads_pypy` (override with `DB_NAME_PYPY`)

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

## 5. Deno

Deno uses the **same shared MySQL** as Django/Go (`DB_*` env vars). Defaults:

| Variable | Default |
|----------|---------|
| `DB_HOST` | `host.docker.internal` |
| `DB_PORT` | `3306` |
| `DB_USERNAME` | `root` |
| `DB_PASSWORD` | `password` |
| `DB_NAME` | `deno_leads` |

```bash
cd deno-app
mise exec -- deno task web      # http://localhost:8004
mise exec -- deno task worker   # queue + schedules
```

- Lead create enqueues a `welcome_email` row in `background_jobs`
- Worker drains the queue and runs `health_check` + `dummy_job` every 1s
- Startup ensures the MySQL database exists, then creates tables

## 6. Bun

Bun uses plain **`.js`** and the **same shared MySQL** as Django/Go/Deno (`DB_*` env vars). Defaults:

| Variable | Default |
|----------|---------|
| `DB_HOST` | `host.docker.internal` |
| `DB_PORT` | `3306` |
| `DB_USERNAME` | `root` |
| `DB_PASSWORD` | `password` |
| `DB_NAME` | `bun_leads` |

```bash
cd bun-app
mise exec -- bun install
mise exec -- bun run web      # http://localhost:8005
mise exec -- bun run worker   # queue + schedules
```

- Lead create enqueues a `welcome_email` row in `background_jobs`
- Worker drains the queue and runs `health_check` + `dummy_job` every 1s
- Startup ensures the MySQL database exists, then creates tables

## 7. Rust

Rust uses **Axum + SQLx** and the **same shared MySQL** (`DB_*` env vars). Defaults:

| Variable | Default |
|----------|---------|
| `DB_HOST` | `host.docker.internal` |
| `DB_PORT` | `3306` |
| `DB_USERNAME` | `root` |
| `DB_PASSWORD` | `password` |
| `DB_NAME` | `rust_leads` |

```bash
cd rust-app
mise exec -- cargo run --release -- web     # http://localhost:8006
mise exec -- cargo run --release -- worker  # queue + schedules
```

## 8. Node.js

Node uses plain **`.js`** (`node:http` + `mysql2`) and the **same shared MySQL**. Defaults:

| Variable | Default |
|----------|---------|
| `DB_HOST` | `host.docker.internal` |
| `DB_PORT` | `3306` |
| `DB_USERNAME` | `root` |
| `DB_PASSWORD` | `password` |
| `DB_NAME` | `node_leads` |

```bash
cd node-app
mise exec -- npm install
mise exec -- npm run web      # http://localhost:8007
mise exec -- npm run worker
```

## 9. .NET 10

ASP.NET Core minimal APIs + MySqlConnector, same shared MySQL (`DB_*`). Defaults:

| Variable | Default |
|----------|---------|
| `DB_HOST` | `host.docker.internal` |
| `DB_PORT` | `3306` |
| `DB_USERNAME` | `root` |
| `DB_PASSWORD` | `password` |
| `DB_NAME` | `dotnet_leads` |

```bash
cd dotnet-app
mise exec -- dotnet run -- web      # http://localhost:8008
mise exec -- dotnet run -- worker
```

## Deploy with Docker Compose

Each app has its own `Dockerfile` and `docker-compose.yml`. Ports do not overlap, so all can run on one host.

| App | Compose directory | Host port | URL |
|-----|-------------------|-----------|-----|
| Spring Boot | `springboot-app/` | **8001** | http://localhost:8001 |
| Pyramid | `pyramid-app/` | **6543** | http://localhost:6543 (web + worker) |
| Django | `django-app/` | **8000** | http://localhost:8000 (web + qcluster) |
| Go | `go-app/` | **8003** | http://localhost:8003 (web + worker) |
| Deno | `deno-app/` | **8004** | http://localhost:8004 (web + worker) |
| Bun | `bun-app/` | **8005** | http://localhost:8005 (web + worker) |
| Rust | `rust-app/` | **8006** | http://localhost:8006 (web + worker) |
| Node.js | `node-app/` | **8007** | http://localhost:8007 (web + worker) |
| .NET 10 | `dotnet-app/` | **8008** | http://localhost:8008 (web + worker) |

Most stacks run **two containers** (web + background worker) for a fair resource comparison. Welcome email is **mocked** everywhere (`[MOCK MAIL]` logs only — no SMTP).

```bash
# Spring Boot (port 8001) — single container
cd springboot-app && docker compose up -d --build

# Pyramid (port 6543) — pyramid-web + pyramid-worker
cd ../pyramid-app && docker compose up -d --build

# Django (port 8000) — django-web + django-qcluster
cd ../django-app && docker compose up -d --build

# Go (port 8003) — go-web + go-worker
cd ../go-app && docker compose up -d --build

# Deno (port 8004) — deno-web + deno-worker
cd ../deno-app && docker compose up -d --build

# Bun (port 8005) — bun-web + bun-worker
cd ../bun-app && docker compose up -d --build

# Rust (port 8006) — rust-web + rust-worker
cd ../rust-app && docker compose up -d --build

# Node.js (port 8007) — node-web + node-worker
cd ../node-app && docker compose up -d --build

# .NET 10 (port 8008) — dotnet-web + dotnet-worker
cd ../dotnet-app && docker compose up -d --build
```

Useful commands (from each app directory):

```bash
docker compose logs -f
docker compose down
```

SQLite data for Spring Boot / Pyramid is in named volumes (`springboot-data`, `pyramid-data`). Most other apps use the shared external MySQL (`DB_*` env vars; see each app’s `.env.example`).

## Notes

- Spring Boot / Pyramid SQLite files live under each app’s `data/` directory (or Docker volume).
- MySQL-backed apps expect a reachable MySQL/MariaDB; override `DB_HOST` if the DB is another Compose service (e.g. `gemtech_mariadb_dev` network alias).
- Use `mise exec -- <command>` if tools are not on your PATH after `mise install`.
- Mail is mocked everywhere (`MockMailClient` / Django `locmem` backend) — safe for server demos.
