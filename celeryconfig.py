import os

from kombu import Exchange, Queue

from settings import AppConfig


class CeleryConfig:
    broker_transport = 'pyamqp'
    broker_use_ssl = not os.getenv('DISABLESSL', False)  # True unless local docker-compose testing
    worker_concurrency = 4
    task_serializer = 'json'
    result_serializer = 'pickle'
    result_backend = 'rpc://'
    accept_content = ['json', 'pickle']
    imports = 'run'
    worker_hijack_root_logger = False
    task_acks_late = True
    worker_prefetch_multiplier = 1
    worker_send_task_events = False
    # Force kill a task if it takes longer than three minutes.
    task_time_limit = 180
    WORKER_ENABLE_REMOTE_CONTROL = True
    result_expires = 3600

    def __init__(self, app_settings: AppConfig):
        self.broker_url = app_settings.BROKER_URL

        queue_args = {'x-queue-type': 'quorum'}
        self.task_queues = (
            Queue(app_settings.ZEUSQUEUE, Exchange(app_settings.ZEUSQUEUE), routing_key=app_settings.ZEUSQUEUE,
                  queue_arguments=queue_args),
        )
