# NexusFlow Backend

NexusFlow is a Django-based business operations platform for accounts, companies, projects, contracts, notifications, and a server-rendered UI using the Django template engine.

## Features
- Custom email-based user model
- Company and department hierarchy
- Projects, tasks, comments, and activity tracking
- Contracts, clients, services, and value calculation
- Django template-based frontend (no separate React app)
- Celery task integration and scheduled jobs

## Local Setup
1. Create and activate virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Copy env file:
   - `copy .env.example .env`
4. Configure `.env` values.
5. Run migrations:
   - `python manage.py migrate`
6. Create superuser:
   - `python manage.py createsuperuser`
7. Run server:
   - `python manage.py runserver`

## Celery and Redis
- Start Redis locally.
- Start worker:
  - `celery -A nexus_flow worker --loglevel=info`
- Start beat:
  - `celery -A nexus_flow beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler`

## Environment Variables
- `DEBUG`: true/false
- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: database connection string
- `REDIS_URL`: redis connection string
- `EMAIL_HOST`: SMTP host
- `EMAIL_PORT`: SMTP port
- `EMAIL_HOST_USER`: SMTP username
- `EMAIL_HOST_PASSWORD`: SMTP password
- `ALLOWED_HOSTS`: comma-separated hosts

## Deployment (Railway/Render)
- Use `Procfile` process types.
- Set all environment variables in platform settings.
- Run migrations as post-deploy step.
- Configure static files and media strategy.

## Project Structure
- `accounts/`
- `companies/`
- `projects/`
- `contracts/`
- `core/`
- `nexus_flow/` (settings, urls, wsgi, celery)
