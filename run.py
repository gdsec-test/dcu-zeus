import logging.config
import os

import yaml
from celery import Celery
from celery.utils.log import get_task_logger
from dcdatabase.kelvinmongo import KelvinMongo
from dcdatabase.phishstorymongo import PhishstoryMongo

from celeryconfig import CeleryConfig
from settings import config_by_name
from zeus.events.email.reporter_mailer import ReporterMailer
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
reporter_mailer = ReporterMailer(config)


def route_request(data, request_type, dual_suspension=False):
    hosted_status = data.get('hosted_status') or data.get('hostedStatus')

    if dual_suspension:
        registrar_brand = data.get('data', {}).get('domainQuery', {}).get('registrar', {}).get('brand')

        if hosted_status == 'HOSTED':
            hosted_suspension = hosted.process(data, request_type)
            registered_suspension = True
            if registrar_brand == 'GODADDY':
                registered_suspension = registered.process(data, request_type)
            return hosted_suspension and registered_suspension
        elif hosted_status in ['REGISTERED', 'FOREIGN']:
            return registered.process(data, request_type)
        else:
            return 'Unable to route request for dual suspension: Hosting Status = {}, Registrar Brand = {}' \
                .format(hosted_status, registrar_brand)
    else:
        if hosted_status == 'HOSTED':
            return hosted.process(data, request_type)
        elif hosted_status in ['REGISTERED', 'FOREIGN']:
            return registered.process(data, request_type)
        else:
            return 'Unable to route request', hosted_status


def get_database_handle():
    return PhishstoryMongo(config)


def get_kelvin_database_handle():
    return KelvinMongo(config.DB_KELVIN, config.DB_KELVIN_URL, config.COLLECTION)


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
def forward_user_gen_complaint(ticket_id):
    data = get_database_handle().get_incident(ticket_id)
    return route_request(data, 'forward_complaint') if data else None


@celery.task()
def customer_warning(ticket_id):
    data = get_database_handle().get_incident(ticket_id)
    return route_request(data, 'customer_warning') if data else None


@celery.task()
def intentionally_malicious(ticket_id, investigator_id):
    data = get_database_handle().get_incident(ticket_id)
    # Add investigator user id to data so its available in _notify_fraud and ssl subscription check
    data['investigator_user_id'] = investigator_id
    return route_request(data, 'intentionally_malicious', True) if data else None


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


@celery.task()
def shopper_compromise(ticket_id, investigator_id):
    data = get_database_handle().get_incident(ticket_id)
    # Add investigator user id to data so its available in _notify_fraud()
    data['investigator_user_id'] = investigator_id
    return route_request(data, 'shopper_compromise') if data else None


@celery.task()
def send_acknowledgement(source, reporter_email):
    return reporter_mailer.send_acknowledgement_email(source, reporter_email)


''' CSAM Tasks '''


@celery.task()
def submitted_to_ncmec(ticket_id):
    data = get_kelvin_database_handle().get_incident(ticket_id)
    return route_request(data, 'ncmec_submitted') if data else None


@celery.task()
def suspend_csam(ticket_id):
    data = get_kelvin_database_handle().get_incident(ticket_id)
    return route_request(data, 'suspend_csam', True) if data else None
