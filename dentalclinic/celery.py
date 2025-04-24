from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dentalclinic.settings')

# Create Celery application instance
app = Celery('dentalclinic')

# Using the Django settings for Celery configuration
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks in all registered Django app configs
app.autodiscover_tasks()

####################################################################################
app.conf.update(
    CELERY_BROKER_URL='redis://localhost:6379/0',  # Broker URL
    CELERY_ACCEPT_CONTENT=['json'],  # Accept JSON format for tasks
    CELERY_TASK_SERIALIZER='json',  # Serialize task results in JSON format
    CELERY_RESULT_BACKEND='redis://localhost:6379/0',  # Redis backend for results
    CELERY_TIMEZONE='UTC',  # Use UTC for task scheduling
)
######################################################################################
# Define the beat schedule inside the Celery app configuration
app.conf.beat_schedule = {
    'move-appointments-every-day': {
        'task': 'appointments.tasks.move_appointments',
        'schedule': crontab(hour=1, minute=55),  # Every day at 1:30 AM
    },
}

# Debug task
@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
