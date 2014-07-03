#!/usr/bin/env python
# encoding: utf-8
from datetime import time

from celery.schedules import crontab

from constants import MQ_HOST
from constants import MQ_USER
from constants import MQ_PASSWORD
from constants import MQ_VHOST

#
# RABBIT-MQ CONFIG
#
BROKER_URL = 'amqp://%s:%s@%s:5672/%s' % \
             (MQ_USER, MQ_PASSWORD, MQ_HOST, MQ_VHOST)

#
# CELERY CONFIG
#
BEAT_NAME = 'import_gtfs_to_fiware'
BEAT_TIME = time(6, 30)
BEAT_QUEUE = 'fiware_queue'

CELERY_IMPORTS = ("fiware.tasks",)
CELERYD_CONCURRENCY = 1
CELERY_RESULT_BACKEND = "amqp"
CELERY_TASK_RESULT_EXPIRES = 60 * 5
CELERYBEAT_SCHEDULE = {
    BEAT_NAME: {
        'task': 'transfer_gtfs',
        'schedule': crontab(hour=BEAT_TIME.hour, minute=BEAT_TIME.minute),
        'args': (),
        'options': {
            'queue': BEAT_QUEUE,
        }
    },
}
