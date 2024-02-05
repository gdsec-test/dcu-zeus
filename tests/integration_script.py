from celery import Celery
from kombu import Exchange, Queue

"""
This script will publish different tasks to the local RabbitMQ devzeus queue
"""


class CeleryConfig:
    broker_transport = 'pyamqp'
    broker_use_ssl = True  # True unless local docker-compose testing
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

    def __init__(self):
        self.broker_url = '' # Add your broker url here

        queue_args = {'x-queue-type': 'quorum'}
        self.task_routes = {
            'run.send_acknowledgement': {
                'queue': Queue('devzeus', Exchange('devzeus'), routing_key='devzeus',
                               queue_arguments=queue_args)
            }
        }


app = Celery()
app.config_from_object(CeleryConfig())

ml_automation_user = 'ml_automation'
ticket_id = 'DCU_TICKET_ID_HERE'

response = app.send_task('run.send_acknowledgement', args=('http://www.sampletest.com', 'ntitus@godaddy.com', True, 10, ))
# response = app.send_task('run.forward_user_gen_complaint', args=(ticket_id,))
# response = app.send_task('run.fraud_new_domain', args=(ticket_id,))
# response = app.send_task('run.fraud_new_hosting_account', args=(ticket_id,))
# response = app.send_task('run.fraud_new_shopper', args=(ticket_id,))
# response = app.send_task('run.intentionally_malicious', args=(ticket_id, ml_automation_user, ))

print(response.ready())
