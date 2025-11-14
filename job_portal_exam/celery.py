from __future__ import annotations
import os
from celery import Celery
 
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "job_portal_exam.settings")
 
app = Celery("job_portal_exam")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()