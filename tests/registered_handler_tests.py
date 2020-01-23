from mock import patch
from nose.tools import assert_false, assert_true

from settings import TestingConfig
from zeus.events.email.foreign_mailer import ForeignMailer
from zeus.events.email.fraud_mailer import FraudMailer
from zeus.events.email.registered_mailer import RegisteredMailer
from zeus.events.email.ssl_mailer import SSLMailer
from zeus.events.support_tools.crm import ThrottledCRM
from zeus.events.suspension.domains import ThrottledDomainService
from zeus.handlers.registered_handler import RegisteredHandler
from zeus.reviews.reviews import BasicReview
from zeus.utils.crmalert import CRMAlert
from zeus.utils.journal import Journal
from zeus.utils.shoplocked import Shoplocked
from zeus.utils.slack import SlackFailures


class TestRegisteredHandler:
    ticket_invalid_type = {'hosted_status': 'REGISTERED'}
    ticket_no_shopper = {'hosted_status': 'REGISTERED', 'type': 'PHISHING'}
    ticket_valid = {'hosted_status': 'REGISTERED', 'type': 'PHISHING', 'data': {
        'domainQuery': {'shopperInfo': {'shopperId': 'test-id'}}}}

    @classmethod
    def setup(cls):
        cls._registered = RegisteredHandler(TestingConfig)

    def test_process_invalid_mapping(self):
        assert_false(self._registered.process({}, 'invalid-request'))

    @patch.object(SlackFailures, 'invalid_hosted_status', return_value=None)
    def test_customer_warning_none(self, invalid_hosting_status):
        assert_false(self._registered.customer_warning({}))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_customer_warning_unsupported_type(self, invalid_abuse_type):
        assert_false(self._registered.customer_warning(self.ticket_invalid_type))

    @patch.object(SlackFailures, 'failed_to_determine_shoppers', return_value=None)
    def test_customer_warning_no_shoppers(self, failed_to_determine_shoppers):
        assert_false(self._registered.customer_warning(self.ticket_no_shopper))

    @patch.object(Journal, 'write', return_value=None)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(RegisteredMailer, 'send_registrant_warning', return_value=False)
    @patch.object(ForeignMailer, 'send_foreign_hosting_notice', return_value=None)
    @patch.object(BasicReview, 'place_in_review', return_value=None)
    def test_customer_warning_failed_registrant_warning(self, review, hosting, registrant, crm, slack, journal):
        assert_false(self._registered.customer_warning(self.ticket_valid))

    @patch.object(SlackFailures, 'invalid_hosted_status', return_value=None)
    def test_intentionally_malicious_none(self, invalid_hosted_status):
        assert_false(self._registered.intentionally_malicious({}))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_intentionally_malicious_unsupported_type(self, invalid_abuse_type):
        assert_false(self._registered.intentionally_malicious(self.ticket_invalid_type))

    @patch.object(SlackFailures, 'failed_to_determine_shoppers', return_value=None)
    def test_intentionally_malicious_no_shoppers(self, failed_to_determine_shoppers):
        assert_false(self._registered.intentionally_malicious(self.ticket_no_shopper))

    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=False)
    def test_intentionally_malicious_already_suspended(self, throttle):
        assert_false(self._registered.intentionally_malicious(self.ticket_valid))

    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(RegisteredMailer, 'send_shopper_intentional_suspension', return_value=False)
    @patch.object(FraudMailer, 'send_malicious_domain_notification', return_value=None)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_intentionally_malicious_failed_shopper_email(self, ssl_mailer, service, crm, fraud, registered, slack, journal, shoplocked):
        assert_false(self._registered.intentionally_malicious(self.ticket_valid))

    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(SlackFailures, 'failed_sending_revocation_email', return_value=None)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(RegisteredMailer, 'send_shopper_intentional_suspension', return_value=True)
    @patch.object(FraudMailer, 'send_malicious_domain_notification', return_value=None)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=False)
    def test_intentionally_malicious_failed_revocation_email(self, ssl_mailer, service, crm, fraud, registered, slack, slack_sll, journal, shoplocked):
        assert_false(self._registered.intentionally_malicious(self.ticket_valid))

    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(RegisteredHandler, '_suspend_domain', return_value=True)
    @patch.object(RegisteredMailer, 'send_shopper_intentional_suspension', return_value=True)
    @patch.object(FraudMailer, 'send_malicious_domain_notification', return_value=None)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_intentionally_malicious_success(self, ssl_mailer, service, crm, fraud, registered, handler, journal, shoplocked, crmalert):
        assert_true(self._registered.intentionally_malicious(self.ticket_valid))

    @patch.object(SlackFailures, 'invalid_hosted_status', return_value=None)
    def test_shopper_compromise_none(self, invalid_hosted_status):
        assert_false(self._registered.shopper_compromise({}))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_shopper_compromise_unsupported_type(self, invalid_abuse_type):
        assert_false(self._registered.shopper_compromise(self.ticket_invalid_type))

    @patch.object(SlackFailures, 'failed_to_determine_shoppers', return_value=None)
    def test_shopper_compromise_no_shoppers(self, failed_to_determine_shoppers):
        assert_false(self._registered.shopper_compromise(self.ticket_no_shopper))

    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(FraudMailer, 'send_malicious_domain_notification', return_value=None)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=False)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_shopper_compromise_already_suspended(self, ssl_mailer, service, crm, fraud, journal, shoplocked):
        assert_false(self._registered.shopper_compromise(self.ticket_valid))

    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(RegisteredMailer, 'send_shopper_compromise_suspension', return_value=False)
    @patch.object(FraudMailer, 'send_malicious_domain_notification', return_value=None)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_shopper_compromise_failed_shopper_email(self, ssl_mailer, service, crm, fraud, registered, slack, journal, shoplocked):
        assert_false(self._registered.shopper_compromise(self.ticket_valid))

    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(RegisteredHandler, '_suspend_domain', return_value=True)
    @patch.object(RegisteredMailer, 'send_shopper_compromise_suspension', return_value=True)
    @patch.object(FraudMailer, 'send_malicious_domain_notification', return_value=None)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_shopper_compromise_success(self, ssl_mailer, service, crm, fraud, registered, handler, journal, shoplocked):
        assert_true(self._registered.shopper_compromise(self.ticket_valid))

    @patch.object(SlackFailures, 'invalid_hosted_status', return_value=None)
    def test_suspend_none(self, invalid_hosted_status):
        assert_false(self._registered.suspend({}))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_suspend_unsupported_type(self, invalid_abuse_type):
        assert_false(self._registered.suspend(self.ticket_invalid_type))

    @patch.object(SlackFailures, 'failed_to_determine_shoppers', return_value=None)
    def test_suspend_no_shoppers(self, failed_to_determine_shoppers):
        assert_false(self._registered.suspend(self.ticket_no_shopper))

    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=False)
    def test_suspend_already_suspended(self, service):
        assert_false(self._registered.suspend(self.ticket_valid))

    @patch.object(Journal, 'write', return_value=None)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(RegisteredMailer, 'send_shopper_suspension', return_value=False)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    def test_suspend_failed_shopper_email(self, service, crm, mailer, slack, journal):
        assert_false(self._registered.suspend(self.ticket_valid))

    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(RegisteredHandler, '_suspend_domain', return_value=True)
    @patch.object(RegisteredMailer, 'send_shopper_suspension', return_value=True)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    def test_suspend_success(self, service, crm, mailer, handler, journal, crmalert):
        assert_true(self._registered.suspend(self.ticket_valid))

    @patch.object(ThrottledDomainService, 'suspend_domain', return_value=True)
    def test_suspend_domain_success(self, service):
        assert_true(self._registered._suspend_domain({}, 'test-id', 'reason'))

    @patch.object(SlackFailures, 'failed_domain_suspension', return_value=None)
    @patch.object(ThrottledDomainService, 'suspend_domain', return_value=False)
    def test_suspend_domain_failed(self, service, slack):
        assert_false(self._registered._suspend_domain({}, 'test-id', 'reason'))
