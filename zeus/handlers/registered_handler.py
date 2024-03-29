import logging.config
from datetime import datetime, timedelta

from csetutils.services.sso import Causes, LockTeamIDs, LockType, SSOClient
from dcdatabase.phishstorymongo import PhishstoryMongo

from settings import AppConfig
from zeus.events.email.foreign_mailer import ForeignMailer
from zeus.events.email.fraud_mailer import FraudMailer
from zeus.events.email.registered_mailer import RegisteredMailer
from zeus.events.email.ssl_mailer import SSLMailer
from zeus.events.support_tools.constants import alert_mappings, note_mappings
from zeus.events.support_tools.crm import ThrottledCRM
from zeus.events.suspension.domains import ThrottledDomainService
from zeus.handlers.interface import Handler
from zeus.reviews.reviews import BasicReview, HighValueReview, SucuriReview
from zeus.utils.crmalert import CRMAlert
from zeus.utils.functions import (get_domain_id_from_dict,
                                  get_high_value_domain_from_dict,
                                  get_host_abuse_email_from_dict,
                                  get_host_brand_from_dict,
                                  get_host_info_from_dict,
                                  get_kelvin_domain_id_from_dict,
                                  get_parent_child_shopper_ids_from_dict,
                                  get_ssl_subscriptions_from_dict,
                                  get_sucuri_product_from_dict)
from zeus.utils.mimir import InfractionTypes, Mimir, RecordTypes
from zeus.utils.shoplocked import Shoplocked
from zeus.utils.shopperapi import ShopperAPI
from zeus.utils.slack import SlackFailures, ThrottledSlack


class RegisteredHandler(Handler):
    TYPES = ['PHISHING', 'MALWARE', 'CHILD_ABUSE']
    HOSTED = 'HOSTED'
    REGISTERED = 'REGISTERED'
    DOMAIN = 'Domain'

    def __init__(self, app_settings: AppConfig):
        self._logger = logging.getLogger('celery.tasks')

        self.registered_mailer = RegisteredMailer(app_settings)
        self.fraud_mailer = FraudMailer(app_settings)
        self.foreign_mailer = ForeignMailer(app_settings)
        self.ssl_mailer = SSLMailer(app_settings)

        self.domain_service = ThrottledDomainService(app_settings)
        self.crm = ThrottledCRM(app_settings)
        self.slack = SlackFailures(ThrottledSlack(app_settings))
        self.shoplocked = Shoplocked(app_settings)
        self.crmalert = CRMAlert(app_settings)
        self.mimir = Mimir(app_settings)
        self.shopper_api = ShopperAPI(app_settings)

        self.basic_review = BasicReview(app_settings)
        self.sucuri_review = SucuriReview(app_settings)
        self.high_value_review = HighValueReview(app_settings)
        self.HOLD_TIME = app_settings.HOLD_TIME
        self.SUCURI_HOLD_TIME = app_settings.SUCURI_HOLD_TIME
        self.HIGH_VALUE_HOLD_TIME = app_settings.HIGH_VALUE_HOLD_TIME
        self.SUCURI_PRODUCT_LIST = app_settings.SUCURI_PRODUCT_LIST
        self.ENTERED_BY = app_settings.ENTERED_BY
        self.PROTECTED_DOMAINS = app_settings.PROTECTED_DOMAINS
        self.FRAUD_REVIEW_TIME = app_settings.FRAUD_REVIEW_TIME
        self._sso_client = SSOClient(app_settings.SSO_URL, app_settings.ZEUS_CLIENT_CERT, app_settings.ZEUS_CLIENT_KEY, app_settings.env)

        self._db = PhishstoryMongo(app_settings)

        self.mapping = {
            'customer_warning': self.customer_warning,
            'forward_complaint': self.forward_user_gen_complaint,
            'intentionally_malicious': self.intentionally_malicious,
            'soft_intentionally_malicious': self.soft_intentionally_malicious,
            'repeat_offender': self.repeat_offender,
            'shopper_compromise': self.shopper_compromise,
            'suspend': self.suspend,
            'suspend_csam': self.suspend_csam
        }

    def process(self, data, request_type):
        if request_type not in self.mapping:
            return False
        return self.mapping[request_type](data)

    def customer_warning(self, data):
        domain = data.get('sourceDomainOrIp')
        subdomain = data.get('sourceSubDomain')
        domain_id = get_domain_id_from_dict(data)
        hosted_brand = get_host_brand_from_dict(data)
        ip = get_host_info_from_dict(data).get('ip')
        recipients = get_host_abuse_email_from_dict(data)
        report_type = data.get('type')
        shopper_id = self.shopper_api.get_shopper_id_from_dict(data)
        shopper_id_list = self.shopper_api.get_list_of_ids_to_notify(data)
        sucuri_product = get_sucuri_product_from_dict(data)
        source = data.get('source')
        ticket_id = data.get('ticketId')
        high_value_domain = get_high_value_domain_from_dict(data)
        portfolio_type = data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('vip', {}).get('portfolioType', '')

        if self._is_domain_protected(domain, action='customer_warning', portfolio_type=portfolio_type):
            return False

        if not self._validate_required_args(data):
            return False

        sucuri_warning = any(sucuri_malware_remover in self.SUCURI_PRODUCT_LIST for sucuri_malware_remover in
                             sucuri_product)
        if sucuri_warning:
            self.sucuri_review.place_in_review(ticket_id, datetime.utcnow() + timedelta(seconds=self.SUCURI_HOLD_TIME),
                                               '72hr_notice_sent')

            if not self.registered_mailer.send_sucuri_reg_warning(ticket_id, domain, domain_id, shopper_id_list,
                                                                  source):
                self.slack.failed_sending_email(domain)
                return False
        elif high_value_domain == 'true':
            self.high_value_review.place_in_review(ticket_id, datetime.utcnow() + timedelta(
                seconds=self.HIGH_VALUE_HOLD_TIME), '72hr_notice_sent')
            if not self.registered_mailer.send_registrant_warning(ticket_id, domain, domain_id, shopper_id_list,
                                                                  source):
                self.slack.failed_sending_email(domain)
                return False
        else:
            self.basic_review.place_in_review(ticket_id, datetime.utcnow() + timedelta(seconds=self.HOLD_TIME),
                                              '24hr_notice_sent')

            if not self.registered_mailer.send_registrant_warning(ticket_id, domain, domain_id, shopper_id_list,
                                                                  source):
                self.slack.failed_sending_email(domain)
                return False

        self.foreign_mailer.send_foreign_hosting_notice(ticket_id, domain, source, hosted_brand, recipients, ip)

        note = note_mappings['registered']['customerWarning']['crm'].format(domain=domain,
                                                                            type=report_type,
                                                                            location=source)
        self.crm.notate_crm_account(shopper_id_list, ticket_id, note, domain, 'customerWarning')

        self.mimir.write(abuse_type=report_type,
                         domain=domain,
                         subdomain=subdomain,
                         domain_id=domain_id,
                         hosted_status=self.REGISTERED,
                         infraction_type=InfractionTypes.customer_warning,
                         record_type=RecordTypes.infraction,
                         shopper_number=shopper_id,
                         ticket_number=ticket_id)

        return True

    def forward_user_gen_complaint(self, data):
        domain = data.get('sourceDomainOrIp')
        domain_id = get_domain_id_from_dict(data)
        shopper_id = self.shopper_api.get_shopper_id_from_dict(data)
        source = data.get('source')
        subdomain = data.get('sourceSubDomain')
        ticket_id = data.get('ticketId')

        if not self._validate_required_args(data):
            return False

        if not self.registered_mailer.send_user_gen_complaint(ticket_id, subdomain, domain_id, shopper_id, source):
            self.slack.failed_sending_email(domain)
            return False
        return True

    def intentionally_malicious(self, data):
        return self._int_mal_worker(data, lock_shopper=True)

    def soft_intentionally_malicious(self, data):
        return self._int_mal_worker(data, lock_shopper=False)

    def _int_mal_worker(self, data: dict, lock_shopper: bool):
        domain = data.get('sourceDomainOrIp')
        subdomain = data.get('sourceSubDomain')
        domain_id = get_domain_id_from_dict(data)
        hosted_status = data.get('hosted_status')
        report_type = data.get('type')
        shopper_id = self.shopper_api.get_shopper_id_from_dict(data)
        shopper_id_list = self.shopper_api.get_list_of_ids_to_notify(data)
        source = data.get('source')
        target = data.get('target')
        ticket_id = data.get('ticketId')
        employee = data.get('investigator_user_id')
        portfolio_type = data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('vip', {}).get('portfolioType', '')

        '''When we have a HOSTED IntMal resolution, Zeus will also suspend the domain name in addition to the host.
        This section accounts for the domain and hosting being in different accounts so we do not take all actions of
        intentionally malicious automation on an account we have not actually put eyes on'''
        hosted_same_shopper = None
        if hosted_status == self.HOSTED:
            if shopper_id == self.shopper_api.get_host_shopper_id_from_dict(data):
                hosted_same_shopper = True
            else:
                return self.suspend(data)

        if self._is_domain_protected(domain, action='intentionally_malicious', portfolio_type=portfolio_type):
            return False

        if not self._validate_required_args(data):
            return False

        if not self.domain_service.can_suspend_domain(domain):
            self._logger.info("Domain {} already suspended".format(domain))
            return False

        note = note_mappings['registered']['intentionallyMalicious']['crm'].format(domain=domain,
                                                                                   type=report_type,
                                                                                   location=source)
        self.crm.notate_crm_account([shopper_id], ticket_id, note, domain, 'intentionallyMalicious')

        '''We do not want to create a second infraction for the domain suspension if the associated hosting is in the
        same customer account'''
        if not hosted_same_shopper:
            self.mimir.write(abuse_type=report_type,
                             domain=domain,
                             subdomain=subdomain,
                             domain_id=domain_id,
                             hosted_status=self.REGISTERED,
                             infraction_type=InfractionTypes.intentionally_malicious,
                             record_type=RecordTypes.infraction,
                             shopper_number=shopper_id,
                             ticket_number=ticket_id)

        self._notify_fraud(data, ticket_id, domain, shopper_id, report_type, source, target)

        ssl_subscription = get_ssl_subscriptions_from_dict(data)
        if ssl_subscription and shopper_id and domain:
            # Send the cert authority ssl revocation email template and log to actions
            self._db.update_actions_sub_document(ticket_id,
                                                 'email sent cert_authority_ssl_revocation',
                                                 data.get('investigator_user_id'))
            if not self.ssl_mailer.send_revocation_email(ticket_id, domain, shopper_id, ssl_subscription):
                self.slack.failed_sending_revocation_email(ticket_id, domain, shopper_id, ssl_subscription)
                return False

        if not self.registered_mailer.send_shopper_intentional_suspension(ticket_id, domain, domain_id, shopper_id_list,
                                                                          report_type):
            self.slack.failed_sending_email(domain)
            return False

        if lock_shopper:
            self._sso_client.lock_idp(
                int(shopper_id),
                LockType.adminTerminated,
                Causes.Policy,
                LockTeamIDs.LtSecurity,
                note_mappings['registered']['intentionallyMalicious']['shoplocked'],
                employee
            )

        alert = alert_mappings['registered']['suspend'].format(domain=domain, type=report_type)
        self.crmalert.create_alert(shopper_id, alert, report_type, self.crmalert.high_severity, domain)

        return self._suspend_domain(domain, ticket_id, note)

    def shopper_compromise(self, data):
        domain = data.get('sourceDomainOrIp')
        subdomain = data.get('sourceSubDomain')
        domain_id = get_domain_id_from_dict(data)
        report_type = data.get('type')
        shopper_id = self.shopper_api.get_shopper_id_from_dict(data)
        shopper_id_list = self.shopper_api.get_list_of_ids_to_notify(data)
        source = data.get('source')
        target = data.get('target')
        ticket_id = data.get('ticketId')
        employee = data.get('investigator_user_id')
        portfolio_type = data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('vip', {}).get('portfolioType', '')

        if self._is_domain_protected(domain, action='shopper_compromise', portfolio_type=portfolio_type):
            return False

        if not self._validate_required_args(data):
            return False

        note = note_mappings['registered']['shopperCompromise']['crm'].format(domain=domain, type=report_type,
                                                                              location=source)
        self.crm.notate_crm_account([shopper_id], ticket_id, note, domain, 'shopperCompromise')

        self.mimir.write(abuse_type=report_type,
                         domain=domain,
                         subdomain=subdomain,
                         domain_id=domain_id,
                         hosted_status=self.REGISTERED,
                         infraction_type=InfractionTypes.shopper_compromise,
                         record_type=RecordTypes.infraction,
                         shopper_number=shopper_id,
                         ticket_number=ticket_id)

        self._notify_fraud(data, ticket_id, domain, shopper_id, report_type, source, target)

        self._sso_client.lock_idp(
            int(shopper_id),
            LockType.adminCompromised,
            Causes.Compromise,
            LockTeamIDs.LtCompromise,
            note_mappings['registered']['shopperCompromise']['shoplocked_lock'],
            employee
        )
        self.shoplocked.scrambler(shopper_id, note_mappings['registered']['shopperCompromise']['shoplocked_scramble'])

        if not self.domain_service.can_suspend_domain(domain):
            self._logger.info("Domain {} already suspended".format(domain))
            return False

        if not self.registered_mailer.send_shopper_compromise_suspension(ticket_id, domain, domain_id, shopper_id_list):
            self.slack.failed_sending_email(domain)
            return False

        return self._suspend_domain(domain, ticket_id, note)

    def repeat_offender(self, data):
        domain = data.get('sourceDomainOrIp')
        subdomain = data.get('sourceSubDomain')
        domain_id = get_domain_id_from_dict(data)
        report_type = data.get('type')
        shopper_id = self.shopper_api.get_shopper_id_from_dict(data)
        shopper_id_list = self.shopper_api.get_list_of_ids_to_notify(data)
        source = data.get('source')
        ticket_id = data.get('ticketId')
        portfolio_type = data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('vip', {}).get('portfolioType', '')

        if self._is_domain_protected(domain, action='repeat_offender', portfolio_type=portfolio_type):
            return False

        elif not self._validate_required_args(data):
            return False

        elif not self.domain_service.can_suspend_domain(domain):
            self._logger.info("Domain {} already suspended".format(domain))
            return False

        note = note_mappings['registered']['repeatOffender']['crm'].format(domain=domain,
                                                                           type=report_type,
                                                                           location=source)
        self.crm.notate_crm_account([shopper_id], ticket_id, note, domain, 'repeatOffender')

        self.mimir.write(abuse_type=report_type,
                         domain=domain,
                         subdomain=subdomain,
                         domain_id=domain_id,
                         hosted_status=self.REGISTERED,
                         infraction_type=InfractionTypes.repeat_offender,
                         record_type=RecordTypes.infraction,
                         shopper_number=shopper_id,
                         ticket_number=ticket_id)

        if not self.registered_mailer.send_repeat_offender_suspension(ticket_id, domain, domain_id,
                                                                      shopper_id_list, source):
            self.slack.failed_sending_email(domain)
            return False

        alert = alert_mappings['registered']['suspend'].format(domain=domain, type=report_type)
        self.crmalert.create_alert(shopper_id, alert, report_type, self.crmalert.high_severity, domain)

        return self._suspend_domain(domain, ticket_id, note)

    def suspend(self, data):
        domain = data.get('sourceDomainOrIp')
        subdomain = data.get('sourceSubDomain')
        domain_id = get_domain_id_from_dict(data)
        report_type = data.get('type')
        shopper_id = self.shopper_api.get_shopper_id_from_dict(data)
        shopper_id_list = self.shopper_api.get_list_of_ids_to_notify(data)
        source = data.get('source')
        ticket_id = data.get('ticketId')
        portfolio_type = data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('vip', {}).get('portfolioType', '')

        if self._is_domain_protected(domain, action='suspend', portfolio_type=portfolio_type):
            return False

        if not self._validate_required_args(data):
            return False

        if not self.domain_service.can_suspend_domain(domain):
            self._logger.info("Domain {} already suspended".format(domain))
            return False

        note = note_mappings['registered']['suspension']['crm'].format(domain=domain,
                                                                       type=report_type,
                                                                       location=source)
        self.crm.notate_crm_account([shopper_id], ticket_id, note, domain, 'suspension')

        self.mimir.write(abuse_type=report_type,
                         domain=domain,
                         subdomain=subdomain,
                         domain_id=domain_id,
                         hosted_status=self.REGISTERED,
                         infraction_type=InfractionTypes.suspended,
                         record_type=RecordTypes.infraction,
                         shopper_number=shopper_id,
                         ticket_number=ticket_id)

        if not self.registered_mailer.send_shopper_suspension(ticket_id, domain, domain_id, shopper_id_list, source,
                                                              report_type):
            self.slack.failed_sending_email(domain)
            return False

        alert = alert_mappings['registered']['suspend'].format(domain=domain, type=report_type)
        self.crmalert.create_alert(shopper_id, alert, report_type, self.crmalert.low_severity, domain)

        return self._suspend_domain(domain, ticket_id, note)

    def suspend_csam(self, data):
        shopper_id = self.shopper_api.get_host_shopper_id_from_dict(data)
        ticket_id = data.get('ticketID')
        domain = data.get('sourceDomainOrIP')
        subdomain = data.get('sourceSubDomain')
        domain_id = get_kelvin_domain_id_from_dict(data)
        report_type = data.get('type')
        hosted_status = data.get('hosted_status')
        portfolio_type = data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('vip', {}).get('portfolioType', '')

        if self._is_domain_protected(domain, action='suspend_csam', portfolio_type=portfolio_type):
            return False

        if not self._validate_required_args(data):
            return False

        if not self.domain_service.can_suspend_domain(domain):
            self._logger.info("Domain {} already suspended".format(domain))
            return False

        note = note_mappings['registered']['suspension']['csam']['crm'].format(domain=domain,
                                                                               type=report_type)
        self.crm.notate_crm_account([shopper_id], ticket_id, note, domain, 'suspension')

        '''We do not want to create a second infraction for the domain suspension if the associated hosting is in the
        same customer account'''
        hosted_same_shopper = None
        if hosted_status == self.HOSTED:
            if shopper_id == self.shopper_api.get_host_shopper_id_from_dict(data):
                hosted_same_shopper = True

        if not hosted_same_shopper:
            self.mimir.write(abuse_type=report_type,
                             domain=domain,
                             subdomain=subdomain,
                             domain_id=domain_id,
                             hosted_status=self.REGISTERED,
                             infraction_type=InfractionTypes.suspended_csam,
                             record_type=RecordTypes.infraction,
                             shopper_number=shopper_id,
                             ticket_number=ticket_id)

        if not self.registered_mailer.send_csam_shopper_suspension(ticket_id, domain, shopper_id, domain_id):
            self.slack.failed_sending_email(ticket_id)
            return False

        return self._suspend_domain(domain, ticket_id, note)

    def _can_fraud_review(self, data):
        # Domains created within FRAUD_REVIEW_TIME number of days can be sent to Fraud for review
        domain_create_date = data.get('data', {}).get('domainQuery', {}).get('registrar', {}).get('domainCreateDate')
        if not domain_create_date:
            domain_create_date = self.EPOCH

        timeframe = datetime.utcnow() - timedelta(days=self.FRAUD_REVIEW_TIME)

        return domain_create_date >= timeframe

    def _is_domain_protected(self, domain, action, portfolio_type: str) -> bool:
        message = f'{action} Action failed for a '
        if domain in self.PROTECTED_DOMAINS and portfolio_type == 'CN':
            message += 'Protected Domain with Portfolio Type "CN": {domain}'
            self.slack.failed_protected_domain_action(domain, action, message)
            return True
        elif domain in self.PROTECTED_DOMAINS:
            message += 'Protected Domain: {domain}'
            self.slack.failed_protected_domain_action(domain, action, message)
            return True
        elif portfolio_type == 'CN':
            message += 'Domain with Portfolio Type "CN": {domain}'
            self.slack.failed_protected_domain_action(domain, action, message)
            return True
        return False

    def _notify_fraud(self, data, ticket_id, domain, shopper_id, report_type, source, target):
        # Notify fraud only if NOT previously sent to fraud, domain created within 90 days, and NOT an apiReseller
        if not data.get('fraud_hold_reason') and self._can_fraud_review(data):
            if not get_parent_child_shopper_ids_from_dict(data):
                # Send the fraud intentionally malicious domain email template and log to actions
                self.fraud_mailer.send_malicious_domain_notification(ticket_id, domain, shopper_id, report_type, source,
                                                                     target)
                self._db.update_actions_sub_document(ticket_id,
                                                     'email sent fraud_intentionally_malicious_domain',
                                                     data.get('investigator_user_id'))

    def _suspend_domain(self, domain, ticket_id, reason):
        self._logger.info("Suspending domain {} for incident {}".format(domain, ticket_id))

        if not self.domain_service.suspend_domain(domain, self.ENTERED_BY, reason):
            self.slack.failed_domain_suspension(domain)
            return False
        return True

    def _validate_required_args(self, data):
        # ticketId for Phishstory and ticketID for Kelvin
        ticket_id = data.get('ticketId', data.get('ticketID'))
        # hosted_status for Phishstory and hostedStatus for Kelvin
        hosted_status = data.get('hosted_status', data.get('hostedStatus'))

        # Because we now have the capability to suspend the domain after suspending the hosing product, we need
        #  to expand on our understanding of valid hosting status, which should now include HOSTING
        if hosted_status not in [self.REGISTERED, self.HOSTED]:
            self.slack.invalid_hosted_status(ticket_id)
        elif data.get('type') not in self.TYPES:
            self.slack.invalid_abuse_type(ticket_id)
        elif not self.shopper_api.get_list_of_ids_to_notify(data):
            self.slack.failed_to_determine_shoppers(ticket_id)
        else:
            return True
        return False
