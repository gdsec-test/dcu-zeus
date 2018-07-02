import logging.config
import os

import yaml
from celery import Celery
from celery.utils.log import get_task_logger
from dcdatabase.phishstorymongo import PhishstoryMongo

from celeryconfig import CeleryConfig
from settings import config_by_name
from zeus.handlers.fraud_handler import FraudHandler
from zeus.handlers.hosted_handler import HostedHandler
from zeus.handlers.registered_handler import RegisteredHandler

# setup logging
path = 'logging.yml'
value = os.getenv('LOG_CFG', None)
if value:
    path = value
if os.path.exists(path):
    with open(path, 'rt') as fraud:
        lconfig = yaml.safe_load(fraud.read())
    logging.config.dictConfig(lconfig)
else:
    logging.basicConfig(level=logging.INFO)

env = os.getenv('sysenv', 'dev')
config = config_by_name[env]()

celery = Celery()
celery.config_from_object(CeleryConfig(config))
_logger = get_task_logger(__name__)

db = PhishstoryMongo(config)

fraud = FraudHandler(config)
hosted = HostedHandler(config)
registered = RegisteredHandler(config)


def route_request(data, request_type):
    if data.get('hosted_status') == 'HOSTED':
        hosted.process(data, request_type)
    elif data.get('hosted_status') == 'REGISTERED':
        registered.process(data, request_type)
    return 'Unsupported Hosted Status'


@celery.task()
def fraud_new_domain(ticket_id):
    data = db.get_incident(ticket_id)
    if not data:
        return
    fraud.new_domain(data)


@celery.task()
def fraud_new_hosting_account(ticket_id):
    data = db.get_incident(ticket_id)
    if not data:
        return
    fraud.new_hosting_account(data)


@celery.task()
def fraud_new_shopper(ticket_id):
    data = db.get_incident(ticket_id)
    if not data:
        return
    fraud.new_shopper(data)


@celery.task()
def customer_warning(ticket_id):
    data = db.get_incident(ticket_id)
    if not data:
        return

    route_request(data.get('hosted_status'), 'customer_warning')


@celery.task()
def intentionally_malicious(ticket_id):
    data = db.get_incident(ticket_id)
    if not data:
        return

    route_request(data.get('hosted_status'), 'intentionally_malicious')


@celery.task()
def suspend(ticket_id):
    data = db.get_incident(ticket_id)
    if not data:
        return

    route_request(data.get('hosted_status'), 'suspend')
