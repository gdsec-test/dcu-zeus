from mock import patch
from nose.tools import assert_equal, assert_false, assert_true

from settings import TestingConfig
from zeus.events.email.hosted_mailer import HostedMailer
from zeus.events.email.ssl_mailer import SSLMailer
from zeus.events.suspension.hosting_service import ThrottledHostingService
from zeus.handlers.hosted_handler import HostedHandler
from zeus.reviews.reviews import BasicReview
from zeus.utils.journal import Journal
from zeus.utils.mimir import Mimir
from zeus.utils.scribe import HostedScribe
from zeus.utils.shoplocked import Shoplocked
from zeus.utils.slack import SlackFailures


class TestHostedHandler:
    phishing = 'PHISHING'
    guid = 'test-guid'
    sid = 'test-id'
    ticket_no_guid = {'type': phishing}
    ticket_no_shopper = {'type': phishing, 'data': {'domainQuery': {'host': {'guid': guid}}}}
    ticket_valid = {'type': phishing,
                    'data': {'domainQuery': {'host': {'guid': guid, 'shopperId': sid}}}}

    @classmethod
    def setup(cls):
        cls._hosted = HostedHandler(TestingConfig)

    def test_process_invalid_mapping(self):
        assert_false(self._hosted.process({}, 'invalid-request'))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_validate_required_args_unsupported_type(self, invalid_abuse_type):
        assert_equal((None, None, None), self._hosted._validate_required_args({}))

    @patch.object(SlackFailures, 'failed_to_determine_guid', return_value=None)
    def test_validate_required_args_no_guid(self, failed_to_determine_guid):
        assert_equal((self.phishing, None, None), self._hosted._validate_required_args(self.ticket_no_guid))

    @patch.object(SlackFailures, 'failed_to_determine_shoppers', return_value=None)
    def test_validate_required_args_no_shopper(self, failed_to_determine_shoppers):
        assert_equal((self.phishing, self.guid, None), self._hosted._validate_required_args(self.ticket_no_shopper))

    def test_validate_required(self):
        assert_equal((self.phishing, self.guid, self.sid), self._hosted._validate_required_args(self.ticket_valid))

    @patch.object(BasicReview, 'place_in_review', return_value=None)
    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_customer_warning_none(self, invalid_abuse_type, review):
        assert_false(self._hosted.customer_warning({}))

    @patch.object(HostedMailer, 'send_hosted_warning', return_value=False)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(HostedScribe, 'customer_warning', return_value=None)
    @patch.object(BasicReview, 'place_in_review', return_value=None)
    def test_customer_warning_failed_registrant_warning(self, review, scribe, slack, mailer):
        assert_false(self._hosted.customer_warning(self.ticket_valid))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_hosted_warning', return_value=True)
    @patch.object(HostedScribe, 'customer_warning', return_value=None)
    @patch.object(BasicReview, 'place_in_review', return_value=None)
    def test_customer_warning_success(self, review, scribe, mailer, journal, mimir):
        assert_true(self._hosted.customer_warning(self.ticket_valid))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_content_removed_none(self, invalid_abuse_type):
        assert_false(self._hosted.content_removed({}))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_content_removed', return_value=False)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(HostedScribe, 'content_removed', return_value=None)
    def test_content_removed_failed_shopper_email(self, scribe, slack, mailer, mimir):
        assert_false(self._hosted.content_removed(self.ticket_valid))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_content_removed', return_value=True)
    @patch.object(HostedScribe, 'content_removed', return_value=None)
    def test_content_removed_success(self, scribe, mailer, mimir):
        assert_true(self._hosted.content_removed(self.ticket_valid))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_intentionally_malicious_none(self, invalid_abuse_type):
        assert_false(self._hosted.intentionally_malicious({}))

    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=False)
    def test_intentionally_malicious_already_suspended(self, can_suspend):
        assert_false(self._hosted.intentionally_malicious(self.ticket_valid))

    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_shopper_hosted_intentional_suspension', return_value=False)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(HostedScribe, 'intentionally_malicious', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_intentionally_malicious_failed_shopper_email(self, ssl_mailer, can_suspend, scribe, slack, mailer, journal, mimir, shoplocked):
        assert_false(self._hosted.intentionally_malicious(self.ticket_valid))

    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(HostedHandler, '_suspend_product', return_value=True)
    @patch.object(HostedMailer, 'send_shopper_hosted_intentional_suspension', return_value=True)
    @patch.object(HostedScribe, 'intentionally_malicious', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_intentionally_malicious_success(self, ssl_mailer, can_suspend, scribe, mailer, suspend, journal, mimir, shoplocked):
        assert_true(self._hosted.intentionally_malicious(self.ticket_valid))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_shopper_compromise_none(self, invalid_abuse_type):
        assert_false(self._hosted.shopper_compromise({}))

    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(HostedScribe, 'shopper_compromise', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=False)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_shopper_compromise_already_suspended(self, ssl_mailer, can_suspend, scribe, journal, mimir, shoplocked):
        assert_false(self._hosted.shopper_compromise(self.ticket_valid))

    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_shopper_compromise_hosted_suspension', return_value=False)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(HostedScribe, 'shopper_compromise', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_shopper_compromise_failed_shopper_email(self, ssl_mailer, can_suspend, scribe, slack, mailer, journal, mimir, shoplocked):
        assert_false(self._hosted.shopper_compromise(self.ticket_valid))

    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(HostedHandler, '_suspend_product', return_value=True)
    @patch.object(HostedMailer, 'send_shopper_compromise_hosted_suspension', return_value=True)
    @patch.object(HostedScribe, 'shopper_compromise', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_shopper_compromise_success(self, ssl_mailer, can_suspend, scribe, mailer, suspend, journal, mimir, shoplocked):
        assert_true(self._hosted.shopper_compromise(self.ticket_valid))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_suspend_none(self, invalid_abuse_type):
        assert_false(self._hosted.suspend({}))

    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=False)
    def test_suspend_already_suspended(self, can_suspend):
        assert_false(self._hosted.suspend(self.ticket_valid))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_shopper_hosted_suspension', return_value=False)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(HostedScribe, 'suspension', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    def test_suspend_failed_shopper_email(self, can_suspend, scribe, slack, mailer, journal, mimir):
        assert_false(self._hosted.suspend(self.ticket_valid))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(HostedHandler, '_suspend_product', return_value=True)
    @patch.object(HostedMailer, 'send_shopper_hosted_suspension', return_value=True)
    @patch.object(HostedScribe, 'suspension', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    def test_suspend_success(self, can_suspend, scribe, mailer, handler, journal, mimir):
        assert_true(self._hosted.suspend(self.ticket_valid))

    @patch.object(SlackFailures, 'failed_hosting_suspension', return_value=None)
    @patch.object(ThrottledHostingService, 'suspend_hosting', return_value=False)
    def test_suspend_product_failure(self, suspend, slack):
        assert_false(self._hosted._suspend_product({}, '', 'test-product'))

    @patch.object(ThrottledHostingService, 'suspend_hosting', return_value=True)
    def test_suspend_product_success(self, suspend):
        assert_true(self._hosted._suspend_product({}, '', 'test-product'))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_repeat_offender_none(self, invalid_abuse_type):
        assert_false(self._hosted.repeat_offender({}))

    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=False)
    def test_repeat_offender_already_suspended(self, can_suspend):
        assert_false(self._hosted.repeat_offender(self.ticket_valid))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_repeat_offender', return_value=False)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(HostedScribe, 'repeat_offender', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    def test_repeat_offender_failed_shopper_email(self, can_suspend, scribe, slack, mailer, journal, mimir):
        assert_false(self._hosted.repeat_offender(self.ticket_valid))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(HostedHandler, '_suspend_product', return_value=True)
    @patch.object(HostedMailer, 'send_repeat_offender', return_value=True)
    @patch.object(HostedScribe, 'repeat_offender', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    def test_repeat_offender_success(self, can_suspend, scribe, mailer, suspend, journal, mimir):
        assert_true(self._hosted.repeat_offender(self.ticket_valid))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_extensive_compromise_none(self, invalid_abuse_type):
        assert_false(self._hosted.extensive_compromise({}))

    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=False)
    def test_extensive_compromise_already_suspended(self, can_suspend):
        assert_false(self._hosted.extensive_compromise(self.ticket_valid))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_extensive_compromise', return_value=False)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(HostedScribe, 'extensive_compromise', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    def test_extensive_compromise_failed_shopper_email(self, can_suspend, scribe, slack, mailer, journal, mimir):
        assert_false(self._hosted.extensive_compromise(self.ticket_valid))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(Journal, 'write', return_value=None)
    @patch.object(HostedHandler, '_suspend_product', return_value=True)
    @patch.object(HostedMailer, 'send_extensive_compromise', return_value=True)
    @patch.object(HostedScribe, 'extensive_compromise', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    def test_extensive_compromise_success(self, can_suspend, scribe, mailer, suspend, journal, mimir):
        assert_true(self._hosted.extensive_compromise(self.ticket_valid))
