import os

from celery import Celery
from celery.schedules import crontab
from dotenv import dotenv_values

config = {
    **dotenv_values(".env"),
    **os.environ,
}

rabbitmq_address = config['RABBITMQ_ADDRESS']
rabbitmq_user = config['RABBITMQ_DEFAULT_USER']
rabbitmq_password = config['RABBITMQ_DEFAULT_PASS']
redis_backend = config['REDIS_CONNECTI§ON_STRING']
celery_broker = f"amqp://{rabbitmq_user}:{rabbitmq_password}@{rabbitmq_address}/"

app = Celery(
    'celery_app',
    broker=celery_broker,
    backend=redis_backend,
    include=['app.celery_tasks.tasks']
)

app.conf.update(
    broker_url=redis_backend,
    timezone='UTC',
)
app.conf.update(
    broker_transport_options={
        'polling_interval': 1.0, 
    },
)

app.conf.beat_schedule = {
    'delete-old-interaction-logs-every-day': {
        'task': 'app.celery_tasks.tasks.delete_old_interaction_logs',
        'schedule': crontab(hour=0, minute=0),
    }
}

app.conf.beat_scheduler = 'celery.beat.PersistentScheduler'
app.conf.beat_scheduler = 'celery.beat.PersistentScheduler'
app.conf.beat_schedule_filename = 'celerybeat-schedule'

@app.task
def check_worker_status():
    print("Checking worker status...")

