# Three POC Lead Management Apps

SQLite-backed Proof-of-Concept web apps (Spring Boot, Pyramid, Django). Each includes Bootstrap 5 CRUD for leads, a background welcome-email simulation, and a 30-minute health/maintenance scheduled task.

Welcome emails are **simulated** (logged only; no SMTP).

| App | Directory | Port |
|-----|-----------|------|
| Spring Boot | `springboot-app/` | http://localhost:8001 |
| Pyramid | `pyramid-app/` | http://localhost:6543 |
| Django | `django-app/` | http://localhost:8000 |

## Prerequisites

Install [mise](https://mise.jdx.dev/), then from this directory:

```bash
mise install
mise exec -- java -version
mise exec -- mvn -version
mise exec -- python --version
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

```bash
cd pyramid-app
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
mkdir -p data
python -c "from leads_app.models import init_db; init_db('sqlite:///./data/leads.db')"
pserve development.ini
```

- Open http://localhost:6543
- Threaded worker logs welcome emails on create
- APScheduler (SQLite job store) runs maintenance every 30 minutes

## 3. Django

```bash
cd django-app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

Run the web server and Django-Q cluster (two terminals):

```bash
python manage.py runserver 8000
python manage.py qcluster
```

- Open http://localhost:8000
- Lead create enqueues `send_welcome_email` via Django-Q
- A Django-Q schedule runs `leads.tasks.run_health_check` every 30 minutes
- You can also run the health check manually: `python manage.py health_check`

## Deploy with Docker Compose

Each app has its own `Dockerfile` and `docker-compose.yml`. Ports do not overlap, so all three can run on one host.

| App | Compose directory | Host port | URL |
|-----|-------------------|-----------|-----|
| Spring Boot | `springboot-app/` | **8001** | http://localhost:8001 |
| Pyramid | `pyramid-app/` | **6543** | http://localhost:6543 |
| Django | `django-app/` | **8000** | http://localhost:8000 |

Welcome email is **mocked** in every app (`[MOCK MAIL]` log lines only — no SMTP).

```bash
# Spring Boot (port 8001)
cd springboot-app && docker compose up -d --build

# Pyramid (port 6543)
cd ../pyramid-app && docker compose up -d --build

# Django web + qcluster (port 8000)
cd ../django-app && docker compose up -d --build
```

Useful commands (from each app directory):

```bash
docker compose logs -f
docker compose down
```

SQLite data is stored in named Docker volumes (`springboot-data`, `pyramid-data`, `django-data`).

## Notes

- SQLite DB files live under each app’s `data/` directory (created at runtime where needed).
- Use `mise exec -- <command>` if tools are not on your PATH after `mise install`.
- Mail is mocked everywhere (`MockMailClient` / Django `locmem` backend) — safe for server demos.
