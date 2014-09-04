#!/usr/bin/env python
# encoding: utf-8
from datetime import time

from celery.schedules import crontab

from utils.constants import MQ_HOST
from utils.constants import MQ_USER
from utils.constants import MQ_PASSWORD
from utils.constants import MQ_VHOST

#
# RABBIT-MQ CONFIG
#
BROKER_URL = 'amqp://%s:%s@%s:5672/%s' % \
             (MQ_USER, MQ_PASSWORD, MQ_HOST, MQ_VHOST)

#
# CELERY CONFIG
#
BEAT_NAME_CB = 'import_gtfs_to_fiware'
BEAT_TIME_CB = time(06, 00)
BEAT_NAME_CKAN = 'import_gtfs_to_ckan'
BEAT_TIME_CKAN = time(06, 30)

BEAT_QUEUE = 'fiware_queue'

CELERY_IMPORTS = ('fiware.tasks', 'ckan.tasks',)
CELERYD_CONCURRENCY = 2
CELERY_RESULT_BACKEND = 'amqp'
CELERY_TASK_RESULT_EXPIRES = 60 * 5
CELERYBEAT_SCHEDULE = {
    BEAT_NAME_CB: {
        'task': 'transfer_gtfs_cb',
        'schedule': crontab(
            hour=BEAT_TIME_CB.hour,
            minute=BEAT_TIME_CB.minute,
        ),
        'args': (),
        'options': {
            'queue': BEAT_QUEUE,
        }
    },
    BEAT_NAME_CKAN: {
        'task': 'transfer_gtfs_ckan',
        'schedule': crontab(
            hour=BEAT_TIME_CKAN.hour,
            minute=BEAT_TIME_CKAN.minute,
        ),
        'args': (),
        'options': {
            'queue': BEAT_QUEUE,
        }
    },
}
