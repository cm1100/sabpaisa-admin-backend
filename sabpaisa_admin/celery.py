import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sabpaisa_admin.settings')

app = Celery('sabpaisa_admin')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps
app.autodiscover_tasks()

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    'process-gateway-sync-queue': {
        'task': 'gateway_sync.tasks.process_sync_queue',
        'schedule': 10.0,  # Every 10 seconds
    },
    'check-pending-transactions': {
        'task': 'gateway_sync.tasks.check_pending_transactions', 
        'schedule': 30.0,  # Every 30 seconds (meets <30s requirement)
    },
    'retry-failed-syncs': {
        'task': 'gateway_sync.tasks.retry_failed_syncs',
        'schedule': 60.0,  # Every minute
    },
}

# Celery configuration for gateway sync optimization
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',
    enable_utc=True,
    task_time_limit=30,  # 30 second timeout per task (meets SLA)
    task_soft_time_limit=25,  # 25 second soft timeout
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=1000,
    task_track_started=True,
    task_acks_late=True,  # Acknowledge task after completion
    worker_disable_rate_limits=True,  # Disable rate limits for speed
)

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')