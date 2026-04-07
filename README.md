# Nexus Flow

Nexus Flow is a Django-based business operations platform with a server-rendered UI.
The project includes account management, company/department structure, projects and tasks,
contracts and clients, notifications, and background task processing with Celery.

## Tech Stack

- Python 3.11+
- Django 5
- PostgreSQL
- Celery + Redis
- WhiteNoise + Gunicorn (production)
- Django Templates (no separate React frontend)

## Repository Structure

- nexus_flow/manage.py: Django management entrypoint
- nexus_flow/nexus_flow/: settings, URLs, WSGI, Celery config
- nexus_flow/accounts/: authentication and user management
- nexus_flow/companies/: companies and departments
- nexus_flow/projects/: projects and tasks
- nexus_flow/contracts/: contracts and clients
- nexus_flow/core/: dashboard, shared models, APIs, common views
- nexus_flow/templates/: server-rendered HTML templates
- nexus_flow/static/: source static files

## Quick Start (Local)

1. Open the backend directory:

```bash
cd nexus_flow
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows (PowerShell):

```powershell
venv/Scripts/Activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create an environment file:

```bash
copy .env.example .env
```

5. Configure your database and service variables in .env (see below).

6. Run migrations:

```bash
python manage.py migrate
```

7. Create an admin user:

```bash
python manage.py createsuperuser
```

8. Start the development server:

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000.

## Environment Variables

The current settings file reads PostgreSQL connection values from DB variables.

Required/important values:

- DEBUG: True/False
- SECRET_KEY: Django secret key
- ALLOWED_HOSTS: comma-separated hosts
- DB_NAME: PostgreSQL database name
- DB_USER: PostgreSQL username
- DB_PASSWORD: PostgreSQL password
- DB_HOST: PostgreSQL host (for example localhost)
- DB_PORT: PostgreSQL port (usually 5432)
- REDIS_URL: Redis URL for Celery broker/backend
- EMAIL_HOST: SMTP host
- EMAIL_PORT: SMTP port
- EMAIL_HOST_USER: SMTP username
- EMAIL_HOST_PASSWORD: SMTP password

Note: .env.example currently includes DATABASE_URL, but settings.py uses DB_NAME/DB_USER/DB_PASSWORD/DB_HOST/DB_PORT.

## Running Celery

From nexus_flow/ directory:

Start worker:

```bash
celery -A nexus_flow worker --loglevel=info
```

Start beat scheduler:

```bash
celery -A nexus_flow beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

Ensure Redis is running before starting worker/beat.

## Running Tests

From nexus_flow/ directory:

```bash
python manage.py test
```

## Production Notes

- Procfile is included for web/worker/beat process definitions.
- Gunicorn is used as the WSGI server.
- WhiteNoise serves collected static files.
- Run collectstatic during deployment:

```bash
python manage.py collectstatic --noinput
```

## License

No license file is currently included in this repository.