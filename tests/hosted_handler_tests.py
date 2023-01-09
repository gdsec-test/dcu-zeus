from datetime import datetime, timedelta
from unittest import TestCase

from dcdatabase.phishstorymongo import PhishstoryMongo
from mock import patch

from zeus.events.email.fraud_mailer import FraudMailer
from zeus.events.email.hosted_mailer import HostedMailer
from zeus.events.email.ssl_mailer import SSLMailer
from zeus.events.suspension.hosting_service import ThrottledHostingService
from zeus.handlers.hosted_handler import HostedHandler
from zeus.reviews.reviews import BasicReview, HighValueReview
from zeus.utils.crmalert import CRMAlert
from zeus.utils.mimir import Mimir
from zeus.utils.scribe import HostedScribe
from zeus.utils.shoplocked import Shoplocked
from zeus.utils.slack import SlackFailures
from settings import config_by_name

config = config_by_name["unit-test"]()


class TestHostedHandler(TestCase):
    phishing = 'PHISHING'
    child_abuse = 'CHILD_ABUSE'
    guid = 'test-guid'
    sid = 'test-id'
    ssl_subscription = '1234'
    domain = 'domain'
    ncmecReportID = '5678'
    current_test_date = datetime.utcnow()
    oldest_valid_fraud_review_test_date = current_test_date - timedelta(days=config.FRAUD_REVIEW_TIME - 1)
    ticket_no_guid = {'type': phishing}
    ticket_no_shopper = {'type': phishing, 'data': {'domainQuery': {'host': {'guid': guid}}}}
    ticket_valid = {'type': phishing, 'sourceDomainOrIp': domain, 'hosted_status': 'HOSTED',
                    'data': {'domainQuery': {'host': {'guid': guid, 'shopperId': sid},
                                             'sslSubscriptions': ssl_subscription}}}
    ticket_fraud_hold = {'type': phishing, 'sourceDomainOrIp': domain, 'fraud_hold_reason': 'test',
                         'data': {'domainQuery': {'host': {'guid': guid, 'shopperId': sid},
                                                  'sslSubscriptions': ssl_subscription}}}
    ticket_valid_api_reseller = {'type': phishing, 'sourceDomainOrIp': domain,
                                 'data': {'domainQuery': {'apiReseller': {'parent': '1234567', 'child': '7654321'},
                                                          'host': {'createdDate': oldest_valid_fraud_review_test_date,
                                                                   'guid': guid, 'shopperId': sid},
                                                          'sslSubscriptions': ssl_subscription}}}
    ticket_no_hold_or_reseller = {'type': phishing, 'sourceDomainOrIp': domain,
                                  'data': {'domainQuery': {'host': {'createdDate': current_test_date,
                                                                    'guid': guid, 'shopperId': sid},
                                                           'sslSubscriptions': ssl_subscription}}}
    ticket_valid_child_abuse = {'type': child_abuse, 'sourceDomainOrIP': domain, 'ncmecReportID': ncmecReportID,
                                'data': {'domainQuery': {'host': {'guid': guid, 'shopperId': sid},
                                                         'sslSubscriptions': ssl_subscription}}}
    ticket_high_value_domain = {'type': phishing, 'sourceDomainOrIp': domain, 'hosted_status': 'HOSTED',
                                'data': {'domainQuery': {'host': {'guid': guid, 'shopperId': sid},
                                                         'isDomainHighValue': 'true',
                                                         'sslSubscriptions': ssl_subscription}}}

    def setUp(self):
        self._hosted = HostedHandler(config)

    def test_process_invalid_mapping(self):
        self.assertFalse(self._hosted.process({}, 'invalid-request'))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_validate_required_args_unsupported_type(self, invalid_abuse_type):
        self.assertEqual((None, None, None), self._hosted._validate_required_args({}))

    @patch.object(SlackFailures, 'failed_to_determine_guid', return_value=None)
    def test_validate_required_args_no_guid(self, failed_to_determine_guid):
        self.assertEqual((self.phishing, None, None), self._hosted._validate_required_args(self.ticket_no_guid))

    @patch.object(SlackFailures, 'failed_to_determine_shoppers', return_value=None)
    def test_validate_required_args_no_shopper(self, failed_to_determine_shoppers):
        self.assertEqual((self.phishing, self.guid, None), self._hosted._validate_required_args(self.ticket_no_shopper))

    def test_validate_required(self):
        self.assertEqual((self.phishing, self.guid, self.sid), self._hosted._validate_required_args(self.ticket_valid))

    def test_validate_required_csam(self):
        self.assertEqual((self.child_abuse, self.guid, self.sid), self._hosted._validate_required_args(self.ticket_valid_child_abuse))

    @patch.object(SlackFailures, 'failed_to_determine_shoppers', return_value=None)
    @patch.object(BasicReview, 'place_in_review', return_value=None)
    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_customer_warning_none(self, invalid_abuse_type, review, slack_infractions):
        self.assertFalse(self._hosted.customer_warning({}))

    @patch.object(HostedMailer, 'send_hosted_warning', return_value=False)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(HostedScribe, 'customer_warning', return_value=None)
    @patch.object(BasicReview, 'place_in_review', return_value=None)
    def test_customer_warning_failed_registrant_warning(self, review, scribe, slack, mailer):
        self.assertFalse(self._hosted.customer_warning(self.ticket_valid))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_hosted_warning', return_value=True)
    @patch.object(HostedScribe, 'customer_warning', return_value=None)
    @patch.object(BasicReview, 'place_in_review', return_value=None)
    def test_customer_warning_success(self, review, scribe, mailer, mimir):
        self.assertTrue(self._hosted.customer_warning(self.ticket_valid))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_hosted_warning', return_value=True)
    @patch.object(HostedScribe, 'customer_warning', return_value=None)
    @patch.object(HighValueReview, 'place_in_review', return_value=None)
    def test_customer_warning_high_value_success(self, review, scribe, mailer, mimir):
        self.assertTrue(self._hosted.customer_warning(self.ticket_high_value_domain))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_content_removed_none(self, invalid_abuse_type):
        self.assertFalse(self._hosted.content_removed({}))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_content_removed', return_value=False)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(HostedScribe, 'content_removed', return_value=None)
    def test_content_removed_failed_shopper_email(self, scribe, slack, mailer, mimir):
        self.assertFalse(self._hosted.content_removed(self.ticket_valid))

    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_content_removed', return_value=True)
    @patch.object(HostedScribe, 'content_removed', return_value=None)
    def test_content_removed_success(self, scribe, mailer, mimir, crmalert):
        self.assertTrue(self._hosted.content_removed(self.ticket_valid))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_intentionally_malicious_none(self, invalid_abuse_type, mock_db):
        self.assertFalse(self._hosted.intentionally_malicious({}))

    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=False)
    def test_intentionally_malicious_already_suspended(self, can_suspend):
        self.assertFalse(self._hosted.intentionally_malicious(self.ticket_valid))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_shopper_hosted_intentional_suspension', return_value=False)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(HostedScribe, 'intentionally_malicious', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_intentionally_malicious_failed_shopper_email_fraud_hold(self, ssl_mailer, can_suspend, scribe,
                                                                     slack, mailer, mimir, shoplocked,
                                                                     mock_db):
        self.assertFalse(self._hosted.intentionally_malicious(self.ticket_fraud_hold))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_shopper_hosted_intentional_suspension', return_value=True)
    @patch.object(SlackFailures, 'failed_sending_revocation_email', return_value=None)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(HostedScribe, 'intentionally_malicious', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=False)
    def test_intentionally_malicious_failed_revocation_email(self, ssl_mailer, can_suspend, scribe, slack,
                                                             slack_ssl, mailer, mimir, shoplocked,
                                                             mock_db):
        self.assertFalse(self._hosted.intentionally_malicious(self.ticket_valid))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedHandler, '_suspend_product', return_value=True)
    @patch.object(HostedMailer, 'send_shopper_hosted_intentional_suspension', return_value=True)
    @patch.object(HostedScribe, 'intentionally_malicious', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_intentionally_malicious_no_termination_email(self, ssl_mailer, can_suspend, scribe, mailer,
                                                          suspend, mimir, shoplocked, crmalert,
                                                          mock_db):
        self.assertTrue(self._hosted.intentionally_malicious(self.ticket_fraud_hold))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedHandler, '_suspend_product', return_value=True)
    @patch.object(HostedMailer, 'send_shopper_hosted_intentional_suspension', return_value=True)
    @patch.object(HostedScribe, 'intentionally_malicious', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_intentionally_malicious_success(self, ssl_mailer, can_suspend, scribe, mailer, suspend,
                                             mimir, shoplocked, crmalert, mock_db):
        self.assertTrue(self._hosted.intentionally_malicious(self.ticket_valid))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(FraudMailer, 'send_malicious_hosting_notification', return_value=None)
    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedHandler, '_suspend_product', return_value=True)
    @patch.object(HostedMailer, 'send_shopper_hosted_intentional_suspension', return_value=True)
    @patch.object(HostedScribe, 'intentionally_malicious', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_intentionally_malicious_no_fraud_email(self, ssl_mailer, can_suspend, scribe, mailer, suspend,
                                                    mimir, shoplocked, crmalert, fraud, mock_db):
        self._hosted.intentionally_malicious(self.ticket_valid_api_reseller)
        fraud.assert_not_called()

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(FraudMailer, 'send_malicious_hosting_notification', return_value=None)
    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedHandler, '_suspend_product', return_value=True)
    @patch.object(HostedMailer, 'send_shopper_hosted_intentional_suspension', return_value=True)
    @patch.object(HostedScribe, 'intentionally_malicious', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_intentionally_malicious_success_fraud_email(self, ssl_mailer, can_suspend, scribe,
                                                         mailer, suspend, mimir, shoplocked, crmalert,
                                                         fraud, mock_db):
        self._hosted.intentionally_malicious(self.ticket_no_hold_or_reseller)
        fraud.assert_called()

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_shopper_compromise_none(self, invalid_abuse_type, mock_db):
        self.assertFalse(self._hosted.shopper_compromise({}))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedScribe, 'shopper_compromise', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=False)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_shopper_compromise_already_suspended(self, ssl_mailer, can_suspend, scribe,
                                                  mimir, shoplocked, mock_db):
        self.assertFalse(self._hosted.shopper_compromise(self.ticket_valid))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_shopper_compromise_hosted_suspension', return_value=False)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(HostedScribe, 'shopper_compromise', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_shopper_compromise_failed_shopper_email(self, ssl_mailer, can_suspend, scribe, slack, mailer,
                                                     mimir, shoplocked, mock_db):
        self.assertFalse(self._hosted.shopper_compromise(self.ticket_valid))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedHandler, '_suspend_product', return_value=True)
    @patch.object(HostedMailer, 'send_shopper_compromise_hosted_suspension', return_value=True)
    @patch.object(HostedScribe, 'shopper_compromise', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_shopper_compromise_success(self, ssl_mailer, can_suspend, scribe, mailer, suspend,
                                        mimir, shoplocked, mopck_db):
        self.assertTrue(self._hosted.shopper_compromise(self.ticket_valid))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(FraudMailer, 'send_malicious_hosting_notification', return_value=None)
    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_shopper_compromise_hosted_suspension', return_value=False)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(HostedScribe, 'shopper_compromise', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_shopper_compromise_no_fraud_email(self, ssl_mailer, can_suspend, scribe, slack, mailer,
                                               mimir, shoplocked, fraud, mock_db):
        self._hosted.shopper_compromise(self.ticket_valid_api_reseller)
        fraud.assert_not_called()

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(FraudMailer, 'send_malicious_hosting_notification', return_value=None)
    @patch.object(Shoplocked, 'adminlock', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedHandler, '_suspend_product', return_value=True)
    @patch.object(HostedMailer, 'send_shopper_compromise_hosted_suspension', return_value=True)
    @patch.object(HostedScribe, 'shopper_compromise', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_shopper_compromise_success_fraud_email(self, ssl_mailer, can_suspend, scribe, mailer,
                                                    suspend, mimir, shoplocked, fraud, mock_db):
        self._hosted.shopper_compromise(self.ticket_no_hold_or_reseller)
        fraud.assert_called()

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_suspend_none(self, invalid_abuse_type):
        self.assertFalse(self._hosted.suspend({}))

    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=False)
    def test_suspend_already_suspended(self, can_suspend):
        self.assertFalse(self._hosted.suspend(self.ticket_valid))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_shopper_hosted_suspension', return_value=False)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(HostedScribe, 'suspension', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    def test_suspend_failed_shopper_email(self, can_suspend, scribe, slack, mailer, mimir):
        self.assertFalse(self._hosted.suspend(self.ticket_valid))

    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedHandler, '_suspend_product', return_value=True)
    @patch.object(HostedMailer, 'send_shopper_hosted_suspension', return_value=True)
    @patch.object(HostedScribe, 'suspension', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    def test_suspend_success(self, can_suspend, scribe, mailer, handler, mimir, crmalert):
        self.assertTrue(self._hosted.suspend(self.ticket_valid))

    @patch.object(SlackFailures, 'failed_hosting_suspension', return_value=None)
    @patch.object(ThrottledHostingService, 'suspend_hosting', return_value=False)
    def test_suspend_product_failure(self, suspend, slack):
        self.assertFalse(self._hosted._suspend_product({}, '', 'test-product'))

    @patch.object(ThrottledHostingService, 'suspend_hosting', return_value=True)
    def test_suspend_product_success(self, suspend):
        self.assertTrue(self._hosted._suspend_product({}, '', 'test-product'))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_repeat_offender_none(self, invalid_abuse_type):
        self.assertFalse(self._hosted.repeat_offender({}))

    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=False)
    def test_repeat_offender_already_suspended(self, can_suspend):
        self.assertFalse(self._hosted.repeat_offender(self.ticket_valid))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_repeat_offender', return_value=False)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(HostedScribe, 'repeat_offender', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    def test_repeat_offender_failed_shopper_email(self, can_suspend, scribe, slack, mailer, mimir):
        self.assertFalse(self._hosted.repeat_offender(self.ticket_valid))

    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedHandler, '_suspend_product', return_value=True)
    @patch.object(HostedMailer, 'send_repeat_offender', return_value=True)
    @patch.object(HostedScribe, 'repeat_offender', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    def test_repeat_offender_success(self, can_suspend, scribe, mailer, suspend, mimir, crmalert):
        self.assertTrue(self._hosted.repeat_offender(self.ticket_valid))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_extensive_compromise_none(self, invalid_abuse_type):
        self.assertFalse(self._hosted.extensive_compromise({}))

    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=False)
    def test_extensive_compromise_already_suspended(self, can_suspend):
        self.assertFalse(self._hosted.extensive_compromise(self.ticket_valid))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedMailer, 'send_extensive_compromise', return_value=False)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(HostedScribe, 'extensive_compromise', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    def test_extensive_compromise_failed_shopper_email(self, can_suspend, scribe, slack, mailer, mimir):
        self.assertFalse(self._hosted.extensive_compromise(self.ticket_valid))

    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedHandler, '_suspend_product', return_value=True)
    @patch.object(HostedMailer, 'send_extensive_compromise', return_value=True)
    @patch.object(HostedScribe, 'extensive_compromise', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    def test_extensive_compromise_success(self, can_suspend, scribe, mailer, suspend, mimir, crmalert):
        self.assertTrue(self._hosted.extensive_compromise(self.ticket_valid))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_ncmec_submitted_none(self, invalid_abuse_type):
        self.assertFalse(self._hosted.ncmec_submitted({}))

    @patch.object(Mimir, 'write', return_value=None)
    def test_ncmec_submitted_success(self, mimir):
        self.assertTrue(self._hosted.ncmec_submitted(self.ticket_valid_child_abuse))

    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(HostedHandler, '_suspend_product', return_value=True)
    @patch.object(HostedMailer, 'send_csam_hosted_suspension', return_value=True)
    @patch.object(HostedScribe, 'suspension', return_value=None)
    @patch.object(ThrottledHostingService, 'can_suspend_hosting_product', return_value=True)
    def test_csam_suspend_success(self, can_suspend, scribe, mailer, handler, mimir, crmalert):
        self.assertTrue(self._hosted.suspend_csam(self.ticket_valid_child_abuse))
