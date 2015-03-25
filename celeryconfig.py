from celery.schedules import crontab
 
CELERYBEAT_SCHEDULE = {
    'every-minute': {
        'task': 'tasks.add',
        'schedule': crontab(minute='*/1'),
        'args': (1,2),
    },
}
