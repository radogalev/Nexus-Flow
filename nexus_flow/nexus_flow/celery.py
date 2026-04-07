import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nexus_flow.settings")

app = Celery("nexus_flow")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
