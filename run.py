import logging.config
import os

import yaml
from celery import Celery
from celery.utils.log import get_task_logger
from dcdatabase.phishstorymongo import PhishstoryMongo

from celeryconfig import CeleryConfig
from settings import config_by_name
from zeus.handlers.foreign_handler import ForeignHandler
from zeus.handlers.fraud_handler import FraudHandler
from zeus.handlers.hosted_handler import HostedHandler
from zeus.handlers.registered_handler import RegisteredHandler

# setup logging
path = 'logging.yaml'
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

fraud = FraudHandler(config)
hosted = HostedHandler(config)
registered = RegisteredHandler(config)
foreign = ForeignHandler(config)


def route_request(data, request_type):
    hosted_status = data.get('hosted_status')

    if hosted_status == 'HOSTED':
        return hosted.process(data, request_type)
    elif hosted_status in ['REGISTERED', 'FOREIGN']:
        return registered.process(data, request_type)

    return 'Unable to route request', hosted_status


def get_database_handle():
    return PhishstoryMongo(config)


''' Fraud Tasks '''


@celery.task()
def fraud_new_domain(ticket_id):
    data = get_database_handle().get_incident(ticket_id)
    return fraud.new_domain(data) if data else None


@celery.task()
def fraud_new_hosting_account(ticket_id):
    data = get_database_handle().get_incident(ticket_id)
    return fraud.new_hosting_account(data) if data else None


@celery.task()
def fraud_new_shopper(ticket_id):
    data = get_database_handle().get_incident(ticket_id)
    return fraud.new_shopper(data) if data else None


''' Foreign Tasks'''


@celery.task()
def foreign_notice(ticket_id):
    data = get_database_handle().get_incident(ticket_id)
    return foreign.foreign_notice(data) if data else None


''' Multi-Handler Tasks '''


@celery.task()
def customer_warning(ticket_id):
    data = get_database_handle().get_incident(ticket_id)
    return route_request(data, 'customer_warning') if data else None


@celery.task()
def intentionally_malicious(ticket_id):
    data = get_database_handle().get_incident(ticket_id)
    return route_request(data, 'intentionally_malicious') if data else None


@celery.task()
def suspend(ticket_id):
    data = get_database_handle().get_incident(ticket_id)
    return route_request(data, 'suspend') if data else None


@celery.task()
def content_removed(ticket_id):
    data = get_database_handle().get_incident(ticket_id)
    return route_request(data, 'content_removed') if data else None


@celery.task()
def repeat_offender(ticket_id):
    data = get_database_handle().get_incident(ticket_id)
    return route_request(data, 'repeat_offender') if data else None


@celery.task()
def extensive_compromise(ticket_id):
    data = get_database_handle().get_incident(ticket_id)
    return route_request(data, 'extensive_compromise') if data else None
