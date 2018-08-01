import logging.config
from datetime import datetime, timedelta

from zeus.events.email.fraud_mailer import FraudMailer
from zeus.events.email.registered_mailer import RegisteredMailer
from zeus.events.support_tools.constants import note_mappings
from zeus.events.support_tools.crm import ThrottledCRM
from zeus.events.suspension.domains import ThrottledDomainService
from zeus.handlers.interface import Handler
from zeus.reviews.reviews import BasicReview
from zeus.utils.functions import get_list_of_ids_to_notify, \
    get_shopper_id_from_dict, \
    get_host_brand_from_dict, \
    get_host_abuse_email_from_dict, get_host_info_from_dict
from zeus.utils.slack import ThrottledSlack, SlackFailures


class RegisteredHandler(Handler):
    TYPES = ['PHISHING', 'MALWARE']
    REGISTERED = 'REGISTERED'
    FOREIGN = 'FOREIGN'

    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)

        self.registered_mailer = RegisteredMailer(app_settings)
        self.fraud_mailer = FraudMailer(app_settings)

        self.domain_service = ThrottledDomainService(app_settings)
        self.crm = ThrottledCRM(app_settings)
        self.slack = SlackFailures(ThrottledSlack(app_settings))

        self.basic_review = BasicReview(app_settings)
        self.HOLD_TIME = app_settings.HOLD_TIME
        self.ENTERED_BY = app_settings.ENTERED_BY

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
        shopper_id_list = get_list_of_ids_to_notify(data)
        ip = get_host_info_from_dict(data).get('ip')
        ticket_id = data.get('ticketId')
        domain = data.get('sourceDomainOrIp')
        report_type = data.get('type')
        source = data.get('source')

        if not self._validate_required_args(data, [self.REGISTERED, self.FOREIGN]):  # Registered or Foreign is OK
            return False

        self.basic_review.place_in_review(ticket_id, datetime.utcnow() + timedelta(seconds=self.HOLD_TIME),
                                          '24hr_notice_sent')
        self.registered_mailer.send_hosting_provider_notice(ticket_id, domain, source, hosted_brand, recipients, ip)

        if data.get('hosted_status') == self.REGISTERED:
            note = note_mappings['registered']['customerWarning']['crm'].format(domain=domain,
                                                                                type=report_type,
                                                                                location=source)
            self.crm.notate_crm_account(shopper_id_list, ticket_id, note)

            if not self.registered_mailer.send_registrant_warning(ticket_id, domain, shopper_id_list, source):
                self.slack.failed_sending_email(ticket_id)
                return False
        return True

    def intentionally_malicious(self, data):
        shopper_id = get_shopper_id_from_dict(data)
        shopper_id_list = get_list_of_ids_to_notify(data)
        ticket_id = data.get('ticketId')
        domain = data.get('sourceDomainOrIp')
        source = data.get('source')
        target = data.get('target')
        report_type = data.get('type')

        if not self._validate_required_args(data):
            return False

        if not self.domain_service.can_suspend_domain(domain):
            self._logger.info("Domain {} already suspended".format(domain))
            return False

        note = note_mappings['registered']['intentionallyMalicious']['crm'].format(domain=domain,
                                                                                   type=report_type,
                                                                                   location=source)
        self.crm.notate_crm_account([shopper_id], ticket_id, note)

        self.fraud_mailer.send_malicious_domain_notification(ticket_id, domain, shopper_id, report_type, source, target)
        if not self.registered_mailer.send_shopper_intentional_suspension(ticket_id, domain, shopper_id_list,
                                                                          report_type):
            self.slack.failed_sending_email(ticket_id)
            return False

        return self._suspend_domain(data, ticket_id, note)

    def suspend(self, data):
        shopper_id = get_shopper_id_from_dict(data)
        shopper_id_list = get_list_of_ids_to_notify(data)
        ticket_id = data.get('ticketId')
        domain = data.get('sourceDomainOrIp')
        source = data.get('source')
        report_type = data.get('type')

        if not self._validate_required_args(data):
            return False

        if not self.domain_service.can_suspend_domain(domain):
            self._logger.info("Domain {} already suspended".format(domain))
            return False

        note = note_mappings['registered']['suspension']['crm'].format(domain=domain,
                                                                       type=report_type,
                                                                       location=source)
        self.crm.notate_crm_account([shopper_id], ticket_id, note)

        if not self.registered_mailer.send_shopper_suspension(ticket_id, domain, shopper_id_list, source, report_type):
            self.slack.failed_sending_email(ticket_id)
            return False

        return self._suspend_domain(data, ticket_id, note)

    def _suspend_domain(self, data, ticket_id, reason):
        domain = data.get('sourceDomainOrIp')

        self._logger.info("Suspending domain {} for incident {}".format(domain, ticket_id))
        if not self.domain_service.suspend_domain(domain, self.ENTERED_BY, reason):
            self.slack.failed_domain_suspension(domain)
            return False
        return True

    def _validate_required_args(self, data, hosted_status=None):
        ticket_id = data.get('ticketId')

        if not hosted_status:
            hosted_status = [self.REGISTERED]

        if data.get('hosted_status') not in hosted_status:
            self.slack.invalid_hosted_status(ticket_id)
        elif data.get('type') not in self.TYPES:
            self.slack.invalid_abuse_type(ticket_id)
        elif not get_list_of_ids_to_notify(data):
            self.slack.failed_to_determine_shoppers(ticket_id)
        else:
            return True
        return False
