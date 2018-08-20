import logging.config
from datetime import datetime, timedelta

from zeus.events.email.fraud_mailer import FraudMailer
from zeus.events.email.hosted_mailer import HostedMailer
from zeus.events.suspension.hosting_service import ThrottledHostingService
from zeus.reviews.reviews import BasicReview
from zeus.utils.functions import get_host_info_from_dict, get_host_shopper_id_from_dict
from zeus.utils.scribe import HostedScribe
from zeus.utils.slack import ThrottledSlack, SlackFailures


class HostedHandler:
    supported_types = ['PHISHING', 'MALWARE']

    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self.hosted_mailer = HostedMailer(app_settings)
        self.fraud_mailer = FraudMailer(app_settings)

        self.hosting_service = ThrottledHostingService(app_settings)
        self.scribe = HostedScribe(app_settings)
        self.slack = SlackFailures(ThrottledSlack(app_settings))

        self.basic_review = BasicReview(app_settings)
        self.HOLD_TIME = app_settings.HOLD_TIME

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

        self.basic_review.place_in_review(ticket_id, datetime.utcnow() + timedelta(seconds=self.HOLD_TIME),
                                          '24hr_notice_sent')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type:  # If any of these were invalid, all values returned as None
            return False

        self.scribe.customer_warning(ticket_id, guid, source, report_type, shopper_id)
        if not self.hosted_mailer.send_hosted_warning(ticket_id, domain, shopper_id, source):
            self.slack.failed_sending_email(domain)
            return False

        return True

    def intentionally_malicious(self, data):
        domain = data.get('sourceDomainOrIp')
        source = data.get('source')
        ticket_id = data.get('ticketId')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type:  # If any of these were invalid, all values returned as None
            return False

        if not self.hosting_service.can_suspend_hosting_product(guid):
            self._logger.info("Hosting {} already suspended".format(guid))
            return False

        self.scribe.intentionally_malicious(ticket_id, guid, source, report_type, shopper_id)
        if not self.hosted_mailer.send_shopper_hosted_intentional_suspension(ticket_id, domain, shopper_id, report_type):
            self.slack.failed_sending_email(domain)
            return False

        return self.suspend_product(data, guid)

    def suspend(self, data):
        domain = data.get('sourceDomainOrIp')
        source = data.get('source')
        ticket_id = data.get('ticketId')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type:  # If any of these were invalid, all values returned as None
            return False

        if not self.hosting_service.can_suspend_hosting_product(guid):
            self._logger.info("Hosting {} already suspended".format(guid))
            return False

        self.scribe.suspension(ticket_id, guid, source, report_type, shopper_id)
        if not self.hosted_mailer.send_shopper_hosted_suspension(ticket_id, domain, shopper_id, source):
            self.slack.failed_sending_email(domain)
            return False

        return self.suspend_product(data, guid)

    def suspend_product(self, data, guid):
        guid = get_host_info_from_dict(data).get('mwpId') or guid
        product = get_host_info_from_dict(data).get('product')

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
        else:
            return report_type, guid, shopper_id
        return None, None, None
