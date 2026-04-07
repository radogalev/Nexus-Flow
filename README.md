# Nexus-Flow

Nexus-Flow is now a Django-only application using the Django template engine for all frontend pages.

## Run locally
1. Open the backend project directory:
	- `cd nexus_flow`
2. Install dependencies:
	- `pip install -r requirements.txt`
3. Apply migrations:
	- `python manage.py migrate`
4. Start the server:
	- `python manage.py runserver`

The app UI is rendered from templates in `nexus_flow/templates/`.