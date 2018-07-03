import os
import urllib

from kombu import Exchange, Queue


class CeleryConfig:
    BROKER_TRANSPORT = 'pyamqp'
    BROKER_USE_SSL = True
    CELERYD_CONCURRENCY = 1
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json', 'pickle']
    CELERY_IMPORTS = 'run'
    CELERYD_HIJACK_ROOT_LOGGER = False
    CELERY_SEND_EVENTS = False

    def __init__(self, app_settings):
        self.BROKER_PASS = urllib.quote(os.getenv('BROKER_PASS', 'password'))
        self.BROKER_URL = 'amqp://02d1081iywc7A:' + self.BROKER_PASS + '@rmq-dcu.int.godaddy.com:5672/grandma'
        self.CELERY_QUEUES = (
            Queue(app_settings.ZEUSQUEUE, Exchange(app_settings.ZEUSQUEUE), routing_key=app_settings.ZEUSQUEUE),
        )
