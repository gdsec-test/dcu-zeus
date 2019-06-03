import logging.config
from datetime import datetime, timedelta

from zeus.events.email.fraud_mailer import FraudMailer
from zeus.events.email.hosted_mailer import HostedMailer
from zeus.events.support_tools.constants import note_mappings
from zeus.events.suspension.hosting_service import ThrottledHostingService
from zeus.reviews.reviews import BasicReview
from zeus.utils.functions import (get_host_info_from_dict,
                                  get_host_shopper_id_from_dict)
from zeus.utils.journal import EventTypes, Journal
from zeus.utils.mimir import InfractionTypes, Mimir
from zeus.utils.scribe import HostedScribe
from zeus.utils.shoplocked import Shoplocked
from zeus.utils.slack import SlackFailures, ThrottledSlack


class HostedHandler:
    supported_types = ['PHISHING', 'MALWARE']

    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self.hosted_mailer = HostedMailer(app_settings)
        self.fraud_mailer = FraudMailer(app_settings)

        self.hosting_service = ThrottledHostingService(app_settings)
        self.scribe = HostedScribe(app_settings)
        self.journal = Journal(app_settings)
        self.mimir = Mimir(app_settings)
        self.slack = SlackFailures(ThrottledSlack(app_settings))
        self.shoplocked = Shoplocked(app_settings)

        self.basic_review = BasicReview(app_settings)
        self.HOLD_TIME = app_settings.HOLD_TIME

        self.mapping = {
            'customer_warning': self.customer_warning,
            'content_removed': self.content_removed,
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
        product = get_host_info_from_dict(data).get('product')

        self.basic_review.place_in_review(ticket_id, datetime.utcnow() + timedelta(seconds=self.HOLD_TIME),
                                          '24hr_notice_sent')

        report_type, guid, shopper_id = self._validate_required_args(data)

        if not shopper_id:
            return False

        # Since we have a shopper_id, try to send the warning email, even if guid or report_type was not found
        if not self.hosted_mailer.send_hosted_warning(ticket_id, domain, shopper_id, source):
            self.slack.failed_sending_email(domain)
            return False

        if not guid or not report_type:
            return False

        self.journal.write(EventTypes.customer_warning, product, domain, report_type,
                           note_mappings['journal']['customerWarning'], [source])

        self.mimir.write(InfractionTypes.customer_warning, shopper_id, ticket_id, domain, guid)
        self.scribe.customer_warning(ticket_id, guid, source, report_type, shopper_id)

        return True

    def content_removed(self, data):
        domain = data.get('sourceDomainOrIp')
        source = data.get('source')
        ticket_id = data.get('ticketId')

        report_type, guid, shopper_id = self._validate_required_args(data)

        if not shopper_id:
            return False

        # Since we have a shopper_id, try to send the notification email, even if guid or report_type was not found
        if not self.hosted_mailer.send_content_removed(ticket_id, domain, shopper_id, source):
            self.slack.failed_sending_email(domain)
            return False

        if not guid or not report_type:
            return False

        self.mimir.write(InfractionTypes.content_removed, shopper_id, ticket_id, domain, guid)
        self.scribe.content_removed(ticket_id, guid, source, report_type, shopper_id)

        return True

    def intentionally_malicious(self, data):
        domain = data.get('sourceDomainOrIp')
        source = data.get('source')
        ticket_id = data.get('ticketId')
        product = get_host_info_from_dict(data).get('product')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type or not guid or not shopper_id:  # Do not proceed if any values are None
            return False

        if not self.hosting_service.can_suspend_hosting_product(guid):
            self._logger.info("Hosting {} already suspended".format(guid))
            return False

        self.journal.write(EventTypes.product_suspension, product, domain, report_type,
                           note_mappings['journal']['intentionallyMalicious'], [source])

        self.mimir.write(InfractionTypes.intentionally_malicious, shopper_id, ticket_id, domain, guid)

        self.scribe.intentionally_malicious(ticket_id, guid, source, report_type, shopper_id)

        if not self.hosted_mailer.send_shopper_hosted_intentional_suspension(ticket_id, domain, shopper_id, report_type):
            self.slack.failed_sending_email(domain)
            return False

        self.shoplocked.adminlock(shopper_id, note_mappings['hosted']['intentionallyMalicious']['shoplocked'])

        return self._suspend_product(data, guid, product)

    def suspend(self, data):
        domain = data.get('sourceDomainOrIp')
        source = data.get('source')
        ticket_id = data.get('ticketId')
        product = get_host_info_from_dict(data).get('product')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type or not guid or not shopper_id:  # Do not proceed if any values are None
            return False

        if not self.hosting_service.can_suspend_hosting_product(guid):
            self._logger.info("Hosting {} already suspended".format(guid))
            return False

        self.journal.write(EventTypes.product_suspension, product, domain, report_type,
                           note_mappings['journal']['suspension'], [source])

        self.mimir.write(InfractionTypes.suspended, shopper_id, ticket_id, domain, guid)

        self.scribe.suspension(ticket_id, guid, source, report_type, shopper_id)
        if not self.hosted_mailer.send_shopper_hosted_suspension(ticket_id, domain, shopper_id, source):
            self.slack.failed_sending_email(domain)
            return False

        return self._suspend_product(data, guid, product)

    def _suspend_product(self, data, guid, product):
        guid = get_host_info_from_dict(data).get('mwpId') or guid

        suspension_result = self.hosting_service.suspend_hosting(product, guid, data)
        if isinstance(suspension_result, str):
            self.slack.failed_hosting_suspension(guid, info=suspension_result)
        elif not suspension_result:
            self.slack.failed_hosting_suspension(guid)
            return False

        return True

    def _validate_required_args(self, data):
        guid = get_host_info_from_dict(data).get('guid')
        shopper_id = get_host_shopper_id_from_dict(data)
        ticket_id = data.get('ticketId')
        report_type = data.get('type')

        if report_type not in self.supported_types:
            self.slack.invalid_abuse_type(ticket_id)
        elif not guid:
            self.slack.failed_to_determine_guid(ticket_id)
        elif not shopper_id:
            self.slack.failed_to_determine_shoppers(ticket_id)
        return report_type, guid, shopper_id
