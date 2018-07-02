import logging.config
from datetime import datetime, timedelta

from zeus.events.email.fraud_mailer import FraudMailer
from zeus.events.email.hosted_mailer import HostedMailer
from zeus.events.support_tools.constants import note_mappings
from zeus.events.support_tools.crm import ThrottledCRM
from zeus.events.support_tools.netvio import Netvio
from zeus.events.suspension.suspension import Suspension
from zeus.persist.persist import Persist
from zeus.reviews.reviews import BasicReview
from zeus.utils.functions import get_host_info_from_dict, get_host_shopper_id_from_dict
from zeus.utils.slack import ThrottledSlack


class HostedHandler:
    supported_types = ['PHISHING', 'MALWARE']

    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self.hosted_mailer = HostedMailer(app_settings)
        self.fraud_mailer = FraudMailer(app_settings)
        self.scribe = Scribe(app_settings)
        self.slack = ThrottledSlack(app_settings)
        self.suspension = Suspension(app_settings)
        self.basic_review = BasicReview(app_settings)
        self.HOLD_TIME = app_settings.HOLD_TIME
        self._throttle = Persist(app_settings.REDIS, app_settings.SUSPEND_HOSTING_LOCK_TIME)

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
        domain = data.get('sourceDomainOrIp')
        source = data.get('source')
        ticket_id = data.get('ticketId')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type:  # If any of these were invalid, all values returned as None
            return False

        self.basic_review.place_in_review(ticket_id, datetime.utcnow() + timedelta(seconds=self.HOLD_TIME),
                                          '24hr_notice_sent')
        self.scribe.customer_warning(ticket_id, guid, source, report_type, shopper_id)
        self.hosted_mailer.send_hosted_warning(ticket_id, domain, shopper_id, source)

    def intentionally_malicious(self, data):
        domain = data.get('sourceDomainOrIp')
        source = data.get('source')
        ticket_id = data.get('ticketId')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type:  # If any of these were invalid, all values returned as None
            return False

        self.scribe.intentionally_malicious(ticket_id, guid, source, report_type, shopper_id)
        self.hosted_mailer.send_shopper_hosted_intentional_suspension(ticket_id, domain, shopper_id, report_type)

        return self.suspend_product(data, guid)

    def suspend(self, data):
        domain = data.get('sourceDomainOrIp')
        ticket_id = data.get('ticketId')
        source = data.get('source')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type:  # If any of these were invalid, all values returned as None
            return False

        self.scribe.suspension(ticket_id, guid, source, report_type, shopper_id)
        self.hosted_mailer.send_shopper_hosted_suspension(ticket_id, domain, shopper_id, source)

        return self.suspend_product(data, guid)

    def suspend_product(self, data, guid):
        guid = get_host_info_from_dict(data).get('mwpId') or guid
        product = get_host_info_from_dict(data).get('product')

        if not self._throttle.can_suspend_hosting_product(guid):
            self._logger.info('Hosting {} already suspended'.format(guid))
            return False

        if not self.suspension.suspend(product, guid):
            message = 'Suspension Failed for Hosting: {}'.format(guid)
            key = '{}_suspend_failed'.format(guid)
            self._send_slack_message(key, message)
            return False
        return True

    def _validate_required_args(self, data):
        guid = get_host_info_from_dict(data).get('guid')
        shopper_id = get_host_shopper_id_from_dict(data)
        ticket_id = data.get('ticketId')
        report_type = data.get('type')

        message = None

        if report_type not in self.supported_types:
            key = '{}_not_valid_hold'.format(ticket_id)
            message = '{} not placed on hold - not a valid ticket type'.format(ticket_id)
            self._send_slack_message(key, message)

        if not guid:
            key = '{}_suspend_failed_no_guid'.format(ticket_id)
            message = 'No action taken for {} - no GUID could be found'.format(ticket_id)
            self._send_slack_message(key, message)

        if not shopper_id:
            key = '{}_suspend_failed_no_shopper'.format(ticket_id)
            message = 'No action taken for {} - unable to determine shopper'.format(ticket_id)
            self._send_slack_message(key, message)

        return (None, None, None) if message else (report_type, guid, shopper_id)

    def _send_slack_message(self, key, message):
        self._logger.warning(message)
        self.slack.send_message(key, message)


class Scribe:
    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self.crm = ThrottledCRM(app_settings)
        self.slack = ThrottledSlack(app_settings)
        self.netvio = Netvio()

    def customer_warning(self, ticket, guid, url, report_type, shopper_id):
        crm_note = note_mappings['hosted']['customerWarning']['crm'].format(guid=guid, type=report_type, location=url)
        self.crm.notate_crm_account(shopper_id, ticket, crm_note)

        netvio_note = note_mappings['hosted']['customerWarning']['netvio'].format(ticket_id=ticket, guid=guid,
                                                                                  type=report_type, location=url)
        if not self.netvio.create_ticket(shopper_id, guid, report_type, netvio_note):
            message = 'Unable to create NetVio ticket for {}'.format(guid)
            key = '{}_create_netvio_failed'.format(guid)
            self.slack.send_message(key, message)

    def suspension(self, ticket, guid, url, report_type, shopper_id):
        crm_note = note_mappings['hosted']['suspension']['crm'].format(guid=guid, type=report_type, location=url)
        self.crm.notate_crm_account(shopper_id, ticket, crm_note)

        netvio_note = note_mappings['hosted']['suspension']['netvio'].format(ticket_id=ticket, guid=guid,
                                                                             type=report_type,
                                                                             location=url)
        if not self.netvio.create_ticket(shopper_id, guid, report_type, netvio_note):
            message = 'Unable to create NetVio ticket for {}'.format(guid)
            key = '{}_create_netvio_failed'.format(guid)
            self.slack.send_message(key, message)

    def intentionally_malicious(self, ticket, guid, url, report_type, shopper_id):
        crm_note = note_mappings['hosted']['intentionallyMalicious']['crm'].format(guid=guid, type=report_type,
                                                                                   location=url)
        self.crm.notate_crm_account(shopper_id, ticket, crm_note)

        netvio_note = note_mappings['hosted']['intentionallyMalicious']['netvio'].format(ticket_id=ticket, guid=guid,
                                                                                         type=report_type, location=url)
        if not self.netvio.create_ticket(shopper_id, guid, report_type, netvio_note):
            message = 'Unable to create NetVio ticket for {}'.format(guid)
            key = '{}_create_netvio_failed'.format(guid)
            self.slack.send_message(key, message)

    def content_removed(self, ticket, guid, url, report_type, shopper_id, content_removed):
        crm_note = note_mappings['hosted']['contentRemoved']['crm'].format(guid=guid, type=report_type, location=url)
        self.crm.notate_crm_account(shopper_id, ticket, crm_note)

        netvio_note = note_mappings['hosted']['contentRemoved']['netvio'].format(ticket_id=ticket, guid=guid,
                                                                                 type=report_type,
                                                                                 location=url,
                                                                                 content_removed=content_removed)
        if not self.netvio.create_ticket(shopper_id, guid, report_type, netvio_note):
            message = 'Unable to create NetVio ticket for {}'.format(guid)
            key = '{}_create_netvio_failed'.format(guid)
            self.slack.send_message(key, message)
