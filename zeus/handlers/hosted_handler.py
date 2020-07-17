import logging.config
from datetime import datetime, timedelta

from zeus.events.email.fraud_mailer import FraudMailer
from zeus.events.email.hosted_mailer import HostedMailer
from zeus.events.email.ssl_mailer import SSLMailer
from zeus.events.support_tools.constants import alert_mappings, note_mappings
from zeus.events.suspension.hosting_service import ThrottledHostingService
from zeus.handlers.interface import Handler
from zeus.reviews.reviews import BasicReview
from zeus.utils.crmalert import CRMAlert
from zeus.utils.functions import (get_host_info_from_dict,
                                  get_host_shopper_id_from_dict,
                                  get_parent_child_shopper_ids_from_dict,
                                  get_ssl_subscriptions_from_dict)
from zeus.utils.journal import EventTypes, Journal
from zeus.utils.mimir import InfractionTypes, Mimir
from zeus.utils.scribe import HostedScribe
from zeus.utils.shoplocked import Shoplocked
from zeus.utils.slack import SlackFailures, ThrottledSlack


class HostedHandler(Handler):
    supported_types = ['PHISHING', 'MALWARE', 'CHILD_ABUSE']

    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self.hosted_mailer = HostedMailer(app_settings)
        self.fraud_mailer = FraudMailer(app_settings)

        self.hosting_service = ThrottledHostingService(app_settings)
        self.scribe = HostedScribe(app_settings)
        self.journal = Journal(app_settings)
        self.mimir = Mimir(app_settings)
        self.ssl_mailer = SSLMailer(app_settings)
        self.slack = SlackFailures(ThrottledSlack(app_settings))
        self.shoplocked = Shoplocked(app_settings)
        self.crmalert = CRMAlert(app_settings)

        self.basic_review = BasicReview(app_settings)
        self.HOLD_TIME = app_settings.HOLD_TIME
        self.FRAUD_REVIEW_TIME = app_settings.FRAUD_REVIEW_TIME

        self.mapping = {
            'customer_warning': self.customer_warning,
            'content_removed': self.content_removed,
            'intentionally_malicious': self.intentionally_malicious,
            'repeat_offender': self.repeat_offender,
            'shopper_compromise': self.shopper_compromise,
            'suspend': self.suspend,
            'extensive_compromise': self.extensive_compromise,
            'ncmec_submitted': self.ncmec_submitted
        }

    def process(self, data, request_type):
        if request_type not in self.mapping:
            return False
        return self.mapping[request_type](data)

    def customer_warning(self, data):
        domain = data.get('sourceDomainOrIp')
        hosted_status = data.get('hosted_status')
        product = get_host_info_from_dict(data).get('product')
        source = data.get('source')
        ticket_id = data.get('ticketId')

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

        abuse_type = data.get('type', '').upper()
        self.mimir.write(abuse_type=abuse_type,
                         domain=domain,
                         guid=guid,
                         hosted_status=hosted_status,
                         infraction_type=InfractionTypes.customer_warning,
                         shopper_number=shopper_id,
                         ticket_number=ticket_id)
        self.scribe.customer_warning(ticket_id, guid, source, report_type, shopper_id)

        return True

    def content_removed(self, data):
        domain = data.get('sourceDomainOrIp')
        hosted_status = data.get('hosted_status')
        source = data.get('source')
        ticket_id = data.get('ticketId')

        report_type, guid, shopper_id = self._validate_required_args(data)

        if not shopper_id:
            return False

        # Since we have a shopper_id, try to send the notification email, even if guid or report_type was not found
        if not self.hosted_mailer.send_content_removed(ticket_id, domain, shopper_id):
            self.slack.failed_sending_email(domain)
            return False

        if not guid or not report_type:
            return False

        abuse_type = data.get('type', '').upper()
        self.mimir.write(abuse_type=abuse_type,
                         domain=domain,
                         guid=guid,
                         hosted_status=hosted_status,
                         infraction_type=InfractionTypes.content_removed,
                         shopper_number=shopper_id,
                         ticket_number=ticket_id)
        self.scribe.content_removed(ticket_id, guid, source, report_type, shopper_id)

        alert = alert_mappings['hosted']['contentRemoved'].format(type=report_type, domain=domain)
        self.crmalert.create_alert(shopper_id, alert, report_type, self.crmalert.low_severity, domain)

        return True

    def intentionally_malicious(self, data):
        domain = data.get('sourceDomainOrIp')
        hosted_status = data.get('hosted_status')
        product = get_host_info_from_dict(data).get('product')
        source = data.get('source')
        target = data.get('target')
        ticket_id = data.get('ticketId')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type or not guid or not shopper_id:  # Do not proceed if any values are None
            return False

        if not self.hosting_service.can_suspend_hosting_product(guid):
            self._logger.info("Hosting {} already suspended".format(guid))
            return False

        self.journal.write(EventTypes.product_suspension, product, domain, report_type,
                           note_mappings['journal']['intentionallyMalicious'], [source])

        abuse_type = data.get('type', '').upper()
        self.mimir.write(abuse_type=abuse_type,
                         domain=domain,
                         guid=guid,
                         hosted_status=hosted_status,
                         infraction_type=InfractionTypes.intentionally_malicious,
                         shopper_number=shopper_id,
                         ticket_number=ticket_id)

        self.scribe.intentionally_malicious(ticket_id, guid, source, report_type, shopper_id)

        self._notify_fraud(data, ticket_id, domain, shopper_id, guid, source, report_type, target)

        ssl_subscription = get_ssl_subscriptions_from_dict(data)
        if ssl_subscription and shopper_id and domain:
            if not self.ssl_mailer.send_revocation_email(ticket_id, domain, shopper_id, ssl_subscription):
                self.slack.failed_sending_revocation_email(ticket_id, domain, shopper_id, ssl_subscription)
                return False

        if not self.hosted_mailer.send_shopper_hosted_intentional_suspension(ticket_id, domain,
                                                                             shopper_id, report_type):
            self.slack.failed_sending_email(domain)
            return False

        self.shoplocked.adminlock(shopper_id, note_mappings['hosted']['intentionallyMalicious']['shoplocked'])

        alert = alert_mappings['hosted']['suspend'].format(domain=domain, type=report_type)
        self.crmalert.create_alert(shopper_id, alert, report_type, self.crmalert.high_severity, domain)

        return self._suspend_product(data, guid, product)

    def shopper_compromise(self, data):
        domain = data.get('sourceDomainOrIp')
        hosted_status = data.get('hosted_status')
        product = get_host_info_from_dict(data).get('product')
        source = data.get('source')
        target = data.get('target')
        ticket_id = data.get('ticketId')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type or not guid or not shopper_id:  # Do not proceed if any values are None
            return False

        self.journal.write(EventTypes.product_suspension, product, domain, report_type,
                           note_mappings['journal']['shopperCompromise'], [source])

        abuse_type = data.get('type', '').upper()
        self.mimir.write(abuse_type=abuse_type,
                         domain=domain,
                         guid=guid,
                         hosted_status=hosted_status,
                         infraction_type=InfractionTypes.shopper_compromise,
                         shopper_number=shopper_id,
                         ticket_number=ticket_id)

        self.scribe.shopper_compromise(ticket_id, guid, source, report_type, shopper_id)

        self._notify_fraud(data, ticket_id, domain, shopper_id, guid, source, report_type, target)

        self.shoplocked.adminlock(shopper_id, note_mappings['hosted']['shopperCompromise']['shoplocked'])

        if not self.hosting_service.can_suspend_hosting_product(guid):
            self._logger.info("Hosting {} already suspended".format(guid))
            return False

        if not self.hosted_mailer.send_shopper_compromise_hosted_suspension(ticket_id, domain, shopper_id):
            self.slack.failed_sending_email(domain)
            return False

        return self._suspend_product(data, guid, product)

    def repeat_offender(self, data):
        domain = data.get('sourceDomainOrIp')
        hosted_status = data.get('hosted_status')
        product = get_host_info_from_dict(data).get('product')
        source = data.get('source')
        ticket_id = data.get('ticketId')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type or not guid or not shopper_id:  # Do not proceed if any values are None
            return False

        if not self.hosting_service.can_suspend_hosting_product(guid):
            self._logger.info("Hosting {} already suspended".format(guid))
            return False

        self.journal.write(EventTypes.product_suspension, product, domain, report_type,
                           note_mappings['journal']['repeatOffender'], [source])

        abuse_type = data.get('type', '').upper()
        self.mimir.write(abuse_type=abuse_type,
                         domain=domain,
                         guid=guid,
                         hosted_status=hosted_status,
                         infraction_type=InfractionTypes.repeat_offender,
                         shopper_number=shopper_id,
                         ticket_number=ticket_id)

        self.scribe.repeat_offender(ticket_id, guid, source, report_type, shopper_id)
        if not self.hosted_mailer.send_repeat_offender(ticket_id, domain, shopper_id, source):
            self.slack.failed_sending_email(domain)
            return False

        alert = alert_mappings['hosted']['suspend'].format(domain=domain, type=report_type)
        self.crmalert.create_alert(shopper_id, alert, report_type, self.crmalert.high_severity, domain)

        return self._suspend_product(data, guid, product)

    def suspend(self, data):
        domain = data.get('sourceDomainOrIp')
        hosted_status = data.get('hosted_status')
        product = get_host_info_from_dict(data).get('product')
        source = data.get('source')
        ticket_id = data.get('ticketId')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type or not guid or not shopper_id:  # Do not proceed if any values are None
            return False

        if not self.hosting_service.can_suspend_hosting_product(guid):
            self._logger.info("Hosting {} already suspended".format(guid))
            return False

        self.journal.write(EventTypes.product_suspension, product, domain, report_type,
                           note_mappings['journal']['suspension'], [source])

        abuse_type = data.get('type', '').upper()
        self.mimir.write(abuse_type=abuse_type,
                         domain=domain,
                         guid=guid,
                         hosted_status=hosted_status,
                         infraction_type=InfractionTypes.suspended,
                         shopper_number=shopper_id,
                         ticket_number=ticket_id)

        self.scribe.suspension(ticket_id, guid, source, report_type, shopper_id)
        if not self.hosted_mailer.send_shopper_hosted_suspension(ticket_id, domain, shopper_id, source):
            self.slack.failed_sending_email(domain)
            return False

        alert = alert_mappings['hosted']['suspend'].format(domain=domain, type=report_type)
        self.crmalert.create_alert(shopper_id, alert, report_type, self.crmalert.low_severity, domain)

        return self._suspend_product(data, guid, product)

    def extensive_compromise(self, data):
        domain = data.get('sourceDomainOrIp')
        hosted_status = data.get('hosted_status')
        product = get_host_info_from_dict(data).get('product')
        source = data.get('source')
        ticket_id = data.get('ticketId')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type or not guid or not shopper_id:  # Do not proceed if any values are None
            return False

        if not self.hosting_service.can_suspend_hosting_product(guid):
            self._logger.info("Hosting {} already suspended".format(guid))
            return False

        self.journal.write(EventTypes.product_suspension, product, domain, report_type,
                           note_mappings['journal']['extensiveCompromise'], [source])

        abuse_type = data.get('type', '').upper()
        self.mimir.write(abuse_type=abuse_type,
                         domain=domain,
                         guid=guid,
                         hosted_status=hosted_status,
                         infraction_type=InfractionTypes.extensive_compromise,
                         shopper_number=shopper_id,
                         ticket_number=ticket_id)

        self.scribe.extensive_compromise(ticket_id, guid, source, report_type, shopper_id)
        if not self.hosted_mailer.send_extensive_compromise(ticket_id, domain, shopper_id):
            self.slack.failed_sending_email(domain)
            return False

        alert = alert_mappings['hosted']['suspend'].format(domain=domain, type=report_type)
        self.crmalert.create_alert(shopper_id, alert, report_type, self.crmalert.low_severity, domain)

        return self._suspend_product(data, guid, product)

    def ncmec_submitted(self, data):
        domain = data.get('sourceDomainOrIP')
        hosted_status = data.get('hosted_status')
        ncmecreport_id = data.get('ncmecReportID')
        ticket_id = data.get('ticketID')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type or not guid or not shopper_id:  # Do not proceed if any values are None
            return False

        note = note_mappings['hosted']['ncmecSubmitted']['mimir'].format(type=report_type, guid=guid)
        abuse_type = data.get('type', '').upper()
        self.mimir.write(abuse_type=abuse_type,
                         domain=domain,
                         guid=guid,
                         hosted_status=hosted_status,
                         infraction_type=InfractionTypes.ncmec_report_submitted,
                         ncmec_report_id=ncmecreport_id,
                         note=note,
                         shopper_number=shopper_id,
                         ticket_number=ticket_id)
        return True

    def _can_fraud_review(self, data):
        # Hosting created within FRAUD_REVIEW_TIME number of days can be sent to Fraud for review
        hosting_create_date = data.get('data', {}).get('domainQuery', {}).get('host', {}).get('createdDate')
        if not hosting_create_date:
            hosting_create_date = self.EPOCH

        timeframe = datetime.utcnow() - timedelta(days=self.FRAUD_REVIEW_TIME)

        return hosting_create_date >= timeframe

    def _notify_fraud(self, data, ticket_id, domain, shopper_id, guid, source, report_type, target):
        # Notify fraud only if NOT previously sent to fraud, domain created within 90 days, and NOT an apiReseller
        if not data.get('fraud_hold_reason') and self._can_fraud_review(data):
            if not get_parent_child_shopper_ids_from_dict(data):
                self.fraud_mailer.send_malicious_hosting_notification(ticket_id, domain, shopper_id, guid, source,
                                                                      report_type, target)

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
        ticket_id = data.get('ticketId') or data.get('ticketID')
        report_type = data.get('type')

        if report_type not in self.supported_types:
            self.slack.invalid_abuse_type(ticket_id)
        elif not guid:
            self.slack.failed_to_determine_guid(ticket_id)
        elif not shopper_id:
            self.slack.failed_to_determine_shoppers(ticket_id)
        return report_type, guid, shopper_id
