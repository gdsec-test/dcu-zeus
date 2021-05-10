from celery import Celery

"""
This script will publish different tasks to the local RabbitMQ devzeus queue
"""


class CeleryConfig:
    broker_transport = 'pyamqp'
    broker_use_ssl = False
    task_serializer = 'pickle'
    result_serializer = 'pickle'
    accept_content = ['json', 'pickle']
    imports = 'run'
    worker_hijack_root_logger = False
    task_acks_late = True
    worker_prefetch_multiplier = 1
    worker_send_task_events = False
    QUEUE = 'queue'
    ZEUSQUEUE = 'devzeus'

    def __init__(self):
        self.task_routes = {
            'run.fraud_new_domain': {self.QUEUE: self.ZEUSQUEUE},
            'run.fraud_new_shopper': {self.QUEUE: self.ZEUSQUEUE},
            'run.fraud_new_hosting_account': {self.QUEUE: self.ZEUSQUEUE},
            'run.customer_warning': {self.QUEUE: self.ZEUSQUEUE},
            'run.forward_user_gen_complaint': {self.QUEUE: self.ZEUSQUEUE},
            'run.intentionally_malicious': {self.QUEUE: self.ZEUSQUEUE}
        }

        self.broker_url = 'amqp://guest@localhost:5672/'  # For local docker-compose testing


app = Celery()
app.config_from_object(CeleryConfig())

ml_automation_user = 'ml_automation'
ticket_id = 'DCU_TICKET_ID_HERE'

response = app.send_task('run.customer_warning', args=(ticket_id,))
# response = app.send_task('run.forward_user_gen_complaint', args=(ticket_id,))
# response = app.send_task('run.fraud_new_domain', args=(ticket_id,))
# response = app.send_task('run.fraud_new_hosting_account', args=(ticket_id,))
# response = app.send_task('run.fraud_new_shopper', args=(ticket_id,))
# response = app.send_task('run.intentionally_malicious', args=(ticket_id, ml_automation_user, ))

print(response)
