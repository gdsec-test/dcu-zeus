import logging.config
import os

import yaml
from celery import Celery
from dcdatabase.kelvinmongo import KelvinMongo
from dcdatabase.phishstorymongo import PhishstoryMongo
from dcustructuredlogging import celerylogger  # noqa: F401

from celeryconfig import CeleryConfig
from settings import config_by_name
from zeus.events.email.reporter_mailer import ReporterMailer
from zeus.events.email.utility_mailer import UtilityMailer
from zeus.handlers.foreign_handler import ForeignHandler
from zeus.handlers.fraud_handler import FraudHandler
from zeus.handlers.hosted_handler import HostedHandler
from zeus.handlers.registered_handler import RegisteredHandler

env = os.getenv('sysenv', 'dev')
config = config_by_name[env]()

celery = Celery()
celery.config_from_object(CeleryConfig(config))

log_level = os.getenv('LOG_LEVEL', 'INFO')


def replace_dict(dict_to_replace):
    """
    Replace empty logging levels in logging.yaml with environment appropriate levels
    :param dict_to_replace: logging.yaml is read into a dict which is passed in
    :return:
    """
    for k, v in dict_to_replace.items():
        if type(v) is dict:
            replace_dict(dict_to_replace[k])
        else:
            if v == 'NOTSET':
                dict_to_replace[k] = log_level


# setup logging
path = 'logging.yaml'
if os.path.exists(path):
    with open(path, 'rt') as f:
        lconfig = yaml.safe_load(f.read())
    replace_dict(lconfig)
    logging.config.dictConfig(lconfig)
else:
    logging.basicConfig(level=logging.INFO)

fraud = FraudHandler(config)
hosted = HostedHandler(config)
registered = RegisteredHandler(config)
foreign = ForeignHandler(config)
utility_mailer = UtilityMailer(config)
reporter_mailer = ReporterMailer(config)

email_limit = 1000


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
    return route_request(data, 'intentionally_malicious', dual_suspension=True) if data else None


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
def shopper_comp_notify(list_of_shoppers):
    failed_tasks = []
    if len(list_of_shoppers) <= email_limit:
        for shopper in list_of_shoppers:
            email_result = utility_mailer.send_account_compromised_email(shopper)
            if not email_result:
                failed_tasks.append(shopper)
    else:
        raise ValueError('Email limit is set to 1,000 recipients at a time. Please try a smaller list')

    return failed_tasks


@celery.task()
def pci_compliance(shopper_and_domain_list):
    failed_tasks = []
    shopper_id = None
    domain = None
    if len(shopper_and_domain_list) <= email_limit:
        for dic in shopper_and_domain_list:
            for val in dic.values():
                if val.isdecimal():
                    shopper_id = val
                else:
                    domain = val

            email_result = utility_mailer.send_pci_compliance_violation(shopper_id, domain)

            if not email_result:
                failed_tasks.append(dic)
    else:
        raise ValueError('Email limit is set to 1,000 recipients at a time. Please try a smaller list')
    return failed_tasks


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
    return route_request(data, 'suspend_csam', dual_suspension=True) if data else None
