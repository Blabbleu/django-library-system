from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.apps import apps
from celery.schedules import timedelta
from celery.schedules import crontab


# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitallibrary.settings')

app = Celery('digitallibrary')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')



