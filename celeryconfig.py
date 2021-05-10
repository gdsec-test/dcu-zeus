import os
from urllib.parse import quote

from kombu import Exchange, Queue


class CeleryConfig:
    broker_transport = 'pyamqp'
    broker_use_ssl = not os.getenv('DISABLESSL', False)  # True unless local docker-compose testing
    worker_concurrency = 4
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json', 'pickle']
    imports = 'run'
    worker_hijack_root_logger = False
    task_acks_late = True
    worker_prefetch_multiplier = 1
    worker_send_task_events = False

    def __init__(self, app_settings):
        self.broker_url = os.getenv('BROKER_URL', None)  # For local docker-compose testing
        if not self.broker_url:
            self.BROKER_PASS = quote(os.getenv('BROKER_PASS', 'password'))
            self.broker_url = 'amqp://02d1081iywc7A:' + self.BROKER_PASS + '@rmq-dcu.int.godaddy.com:5672/grandma'
        self.task_queues = (
            Queue(app_settings.ZEUSQUEUE, Exchange(app_settings.ZEUSQUEUE), routing_key=app_settings.ZEUSQUEUE),
        )
