import logging.config
from datetime import datetime, timedelta

from dcdatabase.phishstorymongo import PhishstoryMongo

from zeus.events.email.fraud_mailer import FraudMailer
from zeus.events.email.hosted_mailer import HostedMailer
from zeus.events.email.ssl_mailer import SSLMailer
from zeus.events.support_tools.constants import alert_mappings, note_mappings
from zeus.events.suspension.hosting_service import ThrottledHostingService
from zeus.handlers.interface import Handler
from zeus.reviews.reviews import BasicReview, HighValueReview, SucuriReview
from zeus.utils.crmalert import CRMAlert
from zeus.utils.functions import (get_high_value_domain_from_dict,
                                  get_host_info_from_dict,
                                  get_host_shopper_id_from_dict,
                                  get_parent_child_shopper_ids_from_dict,
                                  get_ssl_subscriptions_from_dict,
                                  get_sucuri_product_from_dict)
from zeus.utils.mimir import InfractionTypes, Mimir, RecordTypes
from zeus.utils.scribe import HostedScribe
from zeus.utils.shoplocked import Shoplocked
from zeus.utils.slack import SlackFailures, ThrottledSlack


class HostedHandler(Handler):
    supported_types = ['PHISHING', 'MALWARE', 'CHILD_ABUSE']
    HOSTED = 'HOSTED'
    

    def __init__(self, app_settings):
        self._logger = logging.getLogger('celery.tasks')
        self.hosted_mailer = HostedMailer(app_settings)
        self.fraud_mailer = FraudMailer(app_settings)

        self.hosting_service = ThrottledHostingService(app_settings)
        self.scribe = HostedScribe(app_settings)
        self.mimir = Mimir(app_settings)
        self.ssl_mailer = SSLMailer(app_settings)
        self.slack = SlackFailures(ThrottledSlack(app_settings))
        self.shoplocked = Shoplocked(app_settings)
        self.crmalert = CRMAlert(app_settings)

        self.basic_review = BasicReview(app_settings)
        self.sucuri_review = SucuriReview(app_settings)
        self.high_value_review = HighValueReview(app_settings)
        self.HOLD_TIME = app_settings.HOLD_TIME
        self.SUCURI_HOLD_TIME = app_settings.SUCURI_HOLD_TIME
        self.HIGH_VALUE_HOLD_TIME = app_settings.HIGH_VALUE_HOLD_TIME
        self.SUCURI_PRODUCT_LIST = app_settings.SUCURI_PRODUCT_LIST
        self.FRAUD_REVIEW_TIME = app_settings.FRAUD_REVIEW_TIME

        self._db = PhishstoryMongo(app_settings)

        self.mapping = {
            'customer_warning': self.customer_warning,
            'content_removed': self.content_removed,
            'intentionally_malicious': self.intentionally_malicious,
            'repeat_offender': self.repeat_offender,
            'shopper_compromise': self.shopper_compromise,
            'suspend': self.suspend,
            'extensive_compromise': self.extensive_compromise,
            'ncmec_submitted': self.ncmec_submitted,
            'suspend_csam': self.suspend_csam
        }

    def process(self, data, request_type):
        if request_type not in self.mapping:
            return False
        return self.mapping[request_type](data)

    def customer_warning(self, data):
        domain = data.get('sourceDomainOrIp')
        subdomain = data.get('sourceSubDomain')
        source = data.get('source')
        ticket_id = data.get('ticketId')
        sucuri_product = get_sucuri_product_from_dict(data)
        high_value_domain = get_high_value_domain_from_dict(data)

        report_type, guid, shopper_id = self._validate_required_args(data)

        if not shopper_id:
            self.slack.failed_to_determine_shoppers(shopper_id)
            return False

        sucuri_warning = any(sucuri_malware_remover in self.SUCURI_PRODUCT_LIST for sucuri_malware_remover in
                             sucuri_product)

        if sucuri_warning:
            self.sucuri_review.place_in_review(ticket_id, datetime.utcnow() + timedelta(seconds=self.SUCURI_HOLD_TIME),
                                               '72hr_notice_sent')

            # Since we have a shopper_id, try to send the sucuri warning email, even if guid or report_type was not
            # found
            if not self.hosted_mailer.send_sucuri_hosted_warning(ticket_id, domain, shopper_id, source):
                self.slack.failed_sending_email(domain)
                return False
        elif high_value_domain == 'true':
            self.high_value_review.place_in_review(ticket_id, datetime.utcnow() + timedelta(
                seconds=self.HIGH_VALUE_HOLD_TIME), '72hr_notice_sent')

            # Since we have a shopper_id, try to send the warning email, even if guid or report_type was not found
            if not self.hosted_mailer.send_hosted_warning(ticket_id, domain, shopper_id, source):
                self.slack.failed_sending_email(domain)
                return False
        else:
            self.basic_review.place_in_review(ticket_id, datetime.utcnow() + timedelta(seconds=self.HOLD_TIME),
                                              '24hr_notice_sent')

            # Since we have a shopper_id, try to send the warning email, even if guid or report_type was not found
            if not self.hosted_mailer.send_hosted_warning(ticket_id, domain, shopper_id, source):
                self.slack.failed_sending_email(domain)
                return False

        if not guid or not report_type:
            return False

        abuse_type = data.get('type', '').upper()
        self.mimir.write(abuse_type=abuse_type,
                         domain=domain,
                         subdomain=subdomain,
                         guid=guid,
                         hosted_status=self.HOSTED,
                         infraction_type=InfractionTypes.customer_warning,
                         record_type=RecordTypes.infraction,
                         shopper_number=shopper_id,
                         ticket_number=ticket_id)
        self.scribe.customer_warning(ticket_id, guid, source, report_type, shopper_id)

        return True

    def content_removed(self, data):
        domain = data.get('sourceDomainOrIp')
        subdomain = data.get('sourceSubDomain')
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
                         subdomain=subdomain,
                         guid=guid,
                         hosted_status=self.HOSTED,
                         infraction_type=InfractionTypes.content_removed,
                         record_type=RecordTypes.infraction,
                         shopper_number=shopper_id,
                         ticket_number=ticket_id)
        self.scribe.content_removed(ticket_id, guid, source, report_type, shopper_id)

        alert = alert_mappings['hosted']['contentRemoved'].format(type=report_type, domain=domain)
        self.crmalert.create_alert(shopper_id, alert, report_type, self.crmalert.low_severity, domain)

        return True

    def intentionally_malicious(self, data):
        domain = data.get('sourceDomainOrIp')
        subdomain = data.get('sourceSubDomain')
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

        abuse_type = data.get('type', '').upper()
        self.mimir.write(abuse_type=abuse_type,
                         domain=domain,
                         subdomain=subdomain,
                         guid=guid,
                         hosted_status=self.HOSTED,
                         infraction_type=InfractionTypes.intentionally_malicious,
                         record_type=RecordTypes.infraction,
                         shopper_number=shopper_id,
                         ticket_number=ticket_id)

        self.scribe.intentionally_malicious(ticket_id, guid, source, report_type, shopper_id)

        self._notify_fraud(data, ticket_id, domain, shopper_id, guid, source, report_type, target)

        ssl_subscription = get_ssl_subscriptions_from_dict(data)
        if ssl_subscription and shopper_id and domain:
            # Send the cert authority ssl revocation email template and log to actions
            self._db.update_actions_sub_document(ticket_id,
                                                 'email sent cert_authority_ssl_revocation',
                                                 data.get('investigator_user_id'))
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
        subdomain = data.get('sourceSubDomain')
        product = get_host_info_from_dict(data).get('product')
        source = data.get('source')
        target = data.get('target')
        ticket_id = data.get('ticketId')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type or not guid or not shopper_id:  # Do not proceed if any values are None
            return False

        abuse_type = data.get('type', '').upper()
        self.mimir.write(abuse_type=abuse_type,
                         domain=domain,
                         subdomain=subdomain,
                         guid=guid,
                         hosted_status=self.HOSTED,
                         infraction_type=InfractionTypes.shopper_compromise,
                         record_type=RecordTypes.infraction,
                         shopper_number=shopper_id,
                         ticket_number=ticket_id)

        self.scribe.shopper_compromise(ticket_id, guid, source, report_type, shopper_id)

        self._notify_fraud(data, ticket_id, domain, shopper_id, guid, source, report_type, target)

        self.shoplocked.adminlock(shopper_id, note_mappings['hosted']['shopperCompromise']['shoplocked_lock'])
        self.shoplocked.scrambler(shopper_id, note_mappings['hosted']['shopperCompromise']['shoplocked_scramble'])

        if not self.hosting_service.can_suspend_hosting_product(guid):
            self._logger.info("Hosting {} already suspended".format(guid))
            return False

        if not self.hosted_mailer.send_shopper_compromise_hosted_suspension(ticket_id, domain, shopper_id):
            self.slack.failed_sending_email(domain)
            return False

        return self._suspend_product(data, guid, product)

    def repeat_offender(self, data):
        domain = data.get('sourceDomainOrIp')
        subdomain = data.get('sourceSubDomain')
        product = get_host_info_from_dict(data).get('product')
        source = data.get('source')
        ticket_id = data.get('ticketId')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type or not guid or not shopper_id:  # Do not proceed if any values are None
            return False

        if not self.hosting_service.can_suspend_hosting_product(guid):
            self._logger.info("Hosting {} already suspended".format(guid))
            return False

        abuse_type = data.get('type', '').upper()
        self.mimir.write(abuse_type=abuse_type,
                         domain=domain,
                         subdomain=subdomain,
                         guid=guid,
                         hosted_status=self.HOSTED,
                         infraction_type=InfractionTypes.repeat_offender,
                         record_type=RecordTypes.infraction,
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
        subdomain = data.get('sourceSubDomain')
        product = get_host_info_from_dict(data).get('product')
        source = data.get('source')
        ticket_id = data.get('ticketId')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type or not guid or not shopper_id:  # Do not proceed if any values are None
            return False

        if not self.hosting_service.can_suspend_hosting_product(guid):
            self._logger.info("Hosting {} already suspended".format(guid))
            return False

        abuse_type = data.get('type', '').upper()
        self.mimir.write(abuse_type=abuse_type,
                         domain=domain,
                         subdomain=subdomain,
                         guid=guid,
                         hosted_status=self.HOSTED,
                         infraction_type=InfractionTypes.suspended,
                         record_type=RecordTypes.infraction,
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
        subdomain = data.get('sourceSubDomain')
        product = get_host_info_from_dict(data).get('product')
        source = data.get('source')
        ticket_id = data.get('ticketId')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type or not guid or not shopper_id:  # Do not proceed if any values are None
            return False

        if not self.hosting_service.can_suspend_hosting_product(guid):
            self._logger.info("Hosting {} already suspended".format(guid))
            return False

        abuse_type = data.get('type', '').upper()
        self.mimir.write(abuse_type=abuse_type,
                         domain=domain,
                         subdomain=subdomain,
                         guid=guid,
                         hosted_status=self.HOSTED,
                         infraction_type=InfractionTypes.extensive_compromise,
                         record_type=RecordTypes.infraction,
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
        subdomain = data.get('sourceSubDomain')
        ncmecreport_id = data.get('ncmecReportID')
        ticket_id = data.get('ticketID')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type or not guid or not shopper_id:  # Do not proceed if any values are None
            return False

        note = note_mappings['hosted']['ncmecSubmitted']['mimir'].format(domain=domain)
        abuse_type = data.get('type', '').upper()
        self.mimir.write(abuse_type=abuse_type,
                         domain=domain,
                         subdomain=subdomain,
                         guid=guid,
                         hosted_status=self.HOSTED,
                         infraction_type=InfractionTypes.ncmec_report_submitted,
                         ncmec_report_id=ncmecreport_id,
                         note=note,
                         record_type=RecordTypes.ncmec_report,
                         shopper_number=shopper_id,
                         ticket_number=ticket_id)

        return True

    def suspend_csam(self, data):
        domain = data.get('sourceDomainOrIP')
        subdomain = data.get('sourceSubDomain')
        source = data.get('source')
        ticket_id = data.get('ticketID')
        product = get_host_info_from_dict(data).get('product')

        report_type, guid, shopper_id = self._validate_required_args(data)
        if not report_type or not guid or not shopper_id:  # Do not proceed if any values are None
            return False

        if not self.hosting_service.can_suspend_hosting_product(guid):
            self._logger.info("Hosting {} already suspended".format(guid))
            return False

        note = note_mappings['hosted']['suspension']['csam']['mimir'].format(domain=domain)
        self.mimir.write(abuse_type=report_type,
                         domain=domain,
                         subdomain=subdomain,
                         hosted_status=self.HOSTED,
                         infraction_type=InfractionTypes.suspended_csam,
                         note=note,
                         record_type=RecordTypes.infraction,
                         shopper_number=shopper_id,
                         ticket_number=ticket_id)

        self.scribe.suspension(ticket_id, guid, source, report_type, shopper_id)
        if not self.hosted_mailer.send_csam_hosted_suspension(ticket_id, domain, shopper_id):
            self.slack.failed_sending_email(ticket_id)
            return False

        return self._suspend_product(data, guid, product)

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
                # Send the fraud intentionally malicious domain email template and log to actions
                self.fraud_mailer.send_malicious_hosting_notification(ticket_id, domain, shopper_id, guid, source,
                                                                      report_type, target)
                self._db.update_actions_sub_document(ticket_id,
                                                     'email sent fraud_intentionally_malicious_domain',
                                                     data.get('investigator_user_id'))

    def _suspend_product(self, data, guid, product):
        guid = get_host_info_from_dict(data).get('mwpId') or guid
        # TODO: LKM - figure out how to get customer ID here
        customer_id = get_host_info_from_dict(data).get('customerId')
        # TODO: figure out what we actually want to put for 'reason'

        suspension_result = self.hosting_service.suspend_hosting(product, guid, customer_id, 'TODO: Add Reason')
        if isinstance(suspension_result, str):
            self.slack.failed_hosting_suspension(guid, info=suspension_result)
        elif not suspension_result:
            self.slack.failed_hosting_suspension(guid)
            return False

        return True

    def _validate_required_args(self, data):
        guid = get_host_info_from_dict(data).get('guid')
        shopper_id = get_host_shopper_id_from_dict(data)
        # ticketId for Phishstory and ticketID for Kelvin
        ticket_id = data.get('ticketId', data.get('ticketID'))
        report_type = data.get('type')

        if report_type not in self.supported_types:
            self.slack.invalid_abuse_type(ticket_id)
        elif not guid:
            self.slack.failed_to_determine_guid(ticket_id)
        elif not shopper_id:
            self.slack.failed_to_determine_shoppers(ticket_id)
        return report_type, guid, shopper_id
