import logging.config
from datetime import datetime, timedelta

from zeus.events.email.fraud_mailer import FraudMailer
from zeus.events.email.registered_mailer import RegisteredMailer
from zeus.events.support_tools.constants import note_mappings
from zeus.events.support_tools.crm import ThrottledCRM
from zeus.events.suspension.domains import DomainService
from zeus.handlers.interface import Handler
from zeus.persist.persist import Persist
from zeus.reviews.reviews import BasicReview
from zeus.utils.functions import get_list_of_ids_to_notify, \
    get_shopper_id_from_dict, \
    get_host_brand_from_dict, \
    get_host_abuse_email_from_dict, get_host_info_from_dict
from zeus.utils.slack import ThrottledSlack


class RegisteredHandler(Handler):
    supported_types = ['PHISHING', 'MALWARE']

    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self.registered_mailer = RegisteredMailer(app_settings)
        self.fraud_mailer = FraudMailer(app_settings)
        self.crm = ThrottledCRM(app_settings)
        self.slack = ThrottledSlack(app_settings)
        self._throttle = Persist(app_settings.REDIS, app_settings.SUSPEND_DOMAIN_LOCK_TIME)
        self.HOLD_TIME = app_settings.HOLD_TIME
        self.domain_service = DomainService(app_settings.DOMAIN_SERVICE)
        self.ENTERED_BY = app_settings.ENTERED_BY
        self.basic_review = BasicReview(app_settings)

        self.mapping = {
            'customer_warning': self.customer_warning,
            'intentionally_malicious': self.intentionally_malicious,
            'suspend': self.suspend
        }

    def process(self, data, request_type):
        if request_type not in self.mapping:
            return False
        return self.mapping[request_type](data)

    def customer_warning(self, data):
        hosted_brand = get_host_brand_from_dict(data)
        recipients = get_host_abuse_email_from_dict(data)
        ip = get_host_info_from_dict(data).get('ip')
        ticket_id = data.get('ticketId')
        domain = data.get('sourceDomainOrIp')
        report_type = data.get('type')
        source = data.get('source')

        if data.get('hosted_status') not in ['REGISTERED', 'FOREIGN']:
            return False

        if report_type not in self.supported_types:
            return False

        shopper_id_list = get_list_of_ids_to_notify(data)
        if not shopper_id_list:
            self._logger.info("No shoppers found")
            return False

        # Place in Review
        self.basic_review.place_in_review(ticket_id, datetime.utcnow() + timedelta(seconds=self.HOLD_TIME),
                                          '24hr_notice_sent')

        note = note_mappings['registered']['customerWarning']['crm']
        note.format(domain=domain, type=report_type, location=source)
        self.crm.notate_crm_account(shopper_id_list, ticket_id, note)

        # Send emails to 3rd Party Hosting Provider and Registrant
        self.registered_mailer.send_hosting_provider_notice(ticket_id, domain, source, hosted_brand, recipients, ip)
        self.registered_mailer.send_registrant_warning(ticket_id, domain, shopper_id_list, source)

    def intentionally_malicious(self, data):
        shopper_id = get_shopper_id_from_dict(data)
        ticket_id = data.get('ticketId')
        domain = data.get('sourceDomainOrIp')
        source = data.get('source')
        target = data.get('target')
        report_type = data.get('type')

        if data.get('hosted_status') not in ['REGISTERED']:
            return False

        if report_type not in self.supported_types:
            return False

        shopper_id_list = get_list_of_ids_to_notify(data)
        if not shopper_id_list:
            self._slack_no_shopper(ticket_id)
            return False

        note = note_mappings['registered']['intentionallyMalicious']['crm']
        note.format(domain=domain, type=report_type, location=source)
        self.crm.notate_crm_account([shopper_id], ticket_id, note)

        self.fraud_mailer.send_malicious_domain_notification(ticket_id, domain, shopper_id, source, target)
        self.registered_mailer.send_shopper_intentional_suspension(ticket_id, domain, shopper_id_list, report_type)

        self._suspend_domain(data, ticket_id, note)

    def suspend(self, data):
        shopper_id = get_shopper_id_from_dict(data)
        ticket_id = data.get('ticketId')
        domain = data.get('sourceDomainOrIp')
        source = data.get('source')
        report_type = data.get('type')

        if data.get('hosted_status') not in ['REGISTERED']:
            return False

        if report_type not in self.supported_types:
            return False

        shopper_id_list = get_list_of_ids_to_notify(data)
        if not shopper_id_list:
            self._slack_no_shopper(ticket_id)
            return False

        note = note_mappings['registered']['suspension']['crm']
        note.format(domain=domain, type=report_type, location=source)
        self.crm.notate_crm_account([shopper_id], ticket_id, note)

        self.registered_mailer.send_shopper_suspension(ticket_id, domain, shopper_id_list, source, report_type)

        self._suspend_domain(data, ticket_id, note)

    def _suspend_domain(self, data, ticket_id, reason):
        domain = data.get('sourceDomainOrIp')

        if not self._throttle.can_suspend_domain(domain):
            self._logger.info('Domain {} already suspended'.format(domain))
            return False

        self._logger.info('Suspending domain {} for incident {}'.format(domain, ticket_id))
        if not self.domain_service.suspend_domain(domain, self.ENTERED_BY, reason):
            self._slack_suspend_failed(domain)
            return False
        return True

    def _slack_no_shopper(self, ticket_id):
        message = 'No action taken for {} - unable to determine shopper'.format(ticket_id)
        slack_suspension_failure_key = '{}_suspend_failed_no_shopper'.format(ticket_id)

        self._logger.warning(message)
        self.slack.send_message(slack_suspension_failure_key, message)

    def _slack_suspend_failed(self, domain):
        message = 'Suspension Failed for Domain: {}'.format(domain)
        slack_suspension_failure_key = '{}_not_suspended'

        self._logger.warning(message)
        self.slack.send_message(slack_suspension_failure_key.format(domain), message)
