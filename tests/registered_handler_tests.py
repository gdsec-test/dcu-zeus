from datetime import datetime, timedelta
from unittest import TestCase

from csetutils.services.sso import Causes, LockTeamIDs, LockType, SSOClient
from dcdatabase.phishstorymongo import PhishstoryMongo
from mock import patch

from settings import config_by_name
from zeus.events.email.foreign_mailer import ForeignMailer
from zeus.events.email.fraud_mailer import FraudMailer
from zeus.events.email.registered_mailer import RegisteredMailer
from zeus.events.email.ssl_mailer import SSLMailer
from zeus.events.support_tools.crm import ThrottledCRM
from zeus.events.suspension.domains import ThrottledDomainService
from zeus.handlers.registered_handler import RegisteredHandler
from zeus.reviews.reviews import BasicReview, HighValueReview
from zeus.utils.crmalert import CRMAlert
from zeus.utils.mimir import Mimir
from zeus.utils.shopperapi import ShopperAPI
from zeus.utils.slack import SlackFailures

config = config_by_name["unit-test"]()


class TestRegisteredHandler(TestCase):
    childabuse = 'CHILD_ABUSE'
    current_test_date = datetime.utcnow()
    did = 'test-domain-id'
    domain = 'domain'
    domainId = '1234'
    oldest_valid_review_test_date = current_test_date - timedelta(days=config.FRAUD_REVIEW_TIME - 1)
    phishing = 'PHISHING'
    protected_domain = 'myftpupload.com'
    reg = 'REGISTERED'
    sid = '123456789'
    ssl_subscription = '1234'
    ticketID = '4321'
    HOSTED = 'HOSTED'
    JWT = 'JWT_STRING'
    KEY_CREATE_DATE = ''
    KEY_DATA = 'data'
    KEY_DOMAIN = 'sourceDomainOrIp'
    KEY_DOMAIN_DATE = 'domainCreateDate'
    KEY_DOMAIN_ID = 'domainId'
    KEY_DOMAIN_QUERY = 'domainQuery'
    KEY_HOST = 'host'
    KEY_HOSTED_STATUS = 'hosted_status'
    KEY_IS_DOMAIN_HIGH_VALUE = 'isDomainHighValue'
    KEY_PORTFOLIO_TYPE = 'portfolioType'
    KEY_REGISTRAR = 'registrar'
    KEY_SHOPPER_ID = 'shopperId'
    KEY_SHOPPER_INFO = 'shopperInfo'
    KEY_SSL_SUB = 'sslSubscriptions'
    KEY_TYPE = 'type'
    KEY_VIP = 'vip'

    ticket_invalid_type = {KEY_HOSTED_STATUS: reg}
    ticket_no_shopper = {KEY_HOSTED_STATUS: reg, KEY_TYPE: phishing}
    ticket_valid = {KEY_HOSTED_STATUS: reg, KEY_TYPE: phishing, KEY_DOMAIN: domain,
                    KEY_DATA: {
                        KEY_DOMAIN_QUERY: {KEY_SHOPPER_INFO: {KEY_SHOPPER_ID: sid}, KEY_SSL_SUB: ssl_subscription,
                                           KEY_REGISTRAR: {KEY_DOMAIN_ID: did, KEY_DOMAIN_DATE: current_test_date},
                                           KEY_IS_DOMAIN_HIGH_VALUE: 'unsupported'}}}
    ticket_fraud_hold = {'fraud_hold_reason': 'test', KEY_HOSTED_STATUS: reg, KEY_TYPE: phishing,
                         KEY_DOMAIN: domain, KEY_DATA: {KEY_DOMAIN_QUERY: {KEY_SHOPPER_INFO: {KEY_SHOPPER_ID: sid},
                                                                           KEY_SSL_SUB: ssl_subscription}}}
    ticket_protected_domain = {KEY_HOSTED_STATUS: reg, KEY_TYPE: phishing, KEY_DOMAIN: protected_domain,
                               KEY_DATA: {KEY_DOMAIN_QUERY: {KEY_SHOPPER_INFO: {KEY_SHOPPER_ID: sid},
                                                             KEY_SSL_SUB: ssl_subscription}}}
    ticket_protected_domain_with_portfolio_type = {KEY_HOSTED_STATUS: reg, KEY_TYPE: phishing, KEY_DOMAIN: protected_domain,
                                                   KEY_DATA: {KEY_DOMAIN_QUERY: {KEY_SHOPPER_INFO: {KEY_SHOPPER_ID: sid, KEY_VIP: {KEY_PORTFOLIO_TYPE: 'CN'}},
                                                                                 KEY_SSL_SUB: ssl_subscription}}}
    ticket_unprotected_domain_with_portfolio_type = {KEY_HOSTED_STATUS: reg, KEY_TYPE: phishing, KEY_DOMAIN: domain,
                                                     KEY_DATA: {KEY_DOMAIN_QUERY: {KEY_SHOPPER_INFO: {KEY_SHOPPER_ID: sid, KEY_VIP: {KEY_PORTFOLIO_TYPE: 'CN'}},
                                                                                   KEY_SSL_SUB: ssl_subscription}}}
    ticket_valid_api_reseller = {KEY_HOSTED_STATUS: reg, KEY_TYPE: phishing, KEY_DOMAIN: domain,
                                 KEY_DATA: {KEY_DOMAIN_QUERY: {'apiReseller': {'parent': '1234567', 'child': '7654321'},
                                                               KEY_REGISTRAR: {
                                                                   KEY_DOMAIN_DATE: current_test_date},
                                                               KEY_SSL_SUB: ssl_subscription}}}
    ticket_no_hold_or_reseller = {KEY_HOSTED_STATUS: reg, KEY_TYPE: phishing, KEY_DOMAIN: domain,
                                  KEY_DATA: {KEY_DOMAIN_QUERY: {KEY_SHOPPER_INFO: {KEY_SHOPPER_ID: sid},
                                                                KEY_REGISTRAR: {
                                                                    KEY_DOMAIN_DATE: oldest_valid_review_test_date}}}}
    ticket_valid_child_abuse = {KEY_HOSTED_STATUS: reg, KEY_TYPE: childabuse, KEY_DOMAIN: domain, 'ticketID': ticketID,
                                'domain': {KEY_DOMAIN_ID: domainId},
                                KEY_DATA: {KEY_DOMAIN_QUERY: {KEY_SHOPPER_INFO: {KEY_SHOPPER_ID: sid},
                                                              KEY_SSL_SUB: ssl_subscription,
                                                              KEY_REGISTRAR: {KEY_DOMAIN_ID: did}}}}
    ticket_hosted_same_account = {KEY_TYPE: phishing, KEY_DOMAIN: domain, KEY_HOSTED_STATUS: HOSTED,
                                  KEY_DATA: {
                                      KEY_DOMAIN_QUERY: {KEY_HOST: {KEY_SHOPPER_ID: '1357'},
                                                         KEY_SHOPPER_INFO: {KEY_SHOPPER_ID: '1357'},
                                                         KEY_REGISTRAR: {KEY_DOMAIN_DATE: current_test_date},
                                                         KEY_SSL_SUB: ssl_subscription}}}
    ticket_hosted_different_account = {KEY_TYPE: phishing, KEY_DOMAIN: domain, KEY_HOSTED_STATUS: HOSTED,
                                       KEY_DATA: {
                                           KEY_DOMAIN_QUERY: {KEY_HOST: {KEY_SHOPPER_ID: 'different_shopper'},
                                                              KEY_SHOPPER_INFO: {KEY_SHOPPER_ID: '1234'},
                                                              KEY_SSL_SUB: ssl_subscription}}}
    ticket_valid_high_value_domain = {KEY_HOSTED_STATUS: reg,
                                      KEY_TYPE: phishing,
                                      KEY_DOMAIN: domain,
                                      KEY_DATA:
                                          {KEY_DOMAIN_QUERY: {KEY_SHOPPER_INFO: {KEY_SHOPPER_ID: sid},
                                                              KEY_SSL_SUB: ssl_subscription,
                                                              KEY_REGISTRAR: {KEY_DOMAIN_ID: did,
                                                                              KEY_DOMAIN_DATE: current_test_date},
                                                              KEY_IS_DOMAIN_HIGH_VALUE: 'true'}}}

    def setUp(self):
        self._registered = RegisteredHandler(config)

    def test_process_invalid_mapping(self):
        self.assertFalse(self._registered.process({}, 'invalid-request'))

    @patch.object(SlackFailures, 'invalid_hosted_status', return_value=None)
    def test_customer_warning_none(self, invalid_hosting_status):
        self.assertFalse(self._registered.customer_warning({}))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_customer_warning_unsupported_type(self, invalid_abuse_type):
        self.assertFalse(self._registered.customer_warning(self.ticket_invalid_type))

    @patch.object(SlackFailures, 'failed_to_determine_shoppers', return_value=None)
    def test_customer_warning_no_shoppers(self, failed_to_determine_shoppers):
        self.assertFalse(self._registered.customer_warning(self.ticket_no_shopper))

    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(RegisteredMailer, 'send_registrant_warning', return_value=False)
    @patch.object(ForeignMailer, 'send_foreign_hosting_notice', return_value=None)
    @patch.object(BasicReview, 'place_in_review', return_value=None)
    def test_customer_warning_failed_registrant_warning(self, review, hosting, registrant, crm, slack):
        self.assertFalse(self._registered.customer_warning(self.ticket_valid))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(RegisteredMailer, 'send_registrant_warning', return_value=True)
    @patch.object(ForeignMailer, 'send_foreign_hosting_notice', return_value=None)
    @patch.object(HighValueReview, 'place_in_review', return_value=None)
    def test_customer_warning_high_value_domain(self, review, hosting, registrant, crm, slack, mimir):
        self.assertTrue(self._registered.customer_warning(self.ticket_valid_high_value_domain))

    @patch.object(RegisteredHandler, '_validate_required_args', return_value=False)
    def test_forward_user_gen_complaint_failed_arg_validation(self, validation):
        self.assertFalse(self._registered.forward_user_gen_complaint({}))

    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(RegisteredMailer, 'send_user_gen_complaint', return_value=False)
    @patch.object(RegisteredHandler, '_validate_required_args', return_value=True)
    def test_forward_user_gen_complaint_failed_send_mail(self, validation, registrant, slack):
        self.assertFalse(self._registered.forward_user_gen_complaint({}))

    @patch.object(RegisteredMailer, 'send_user_gen_complaint', return_value=True)
    @patch.object(RegisteredHandler, '_validate_required_args', return_value=True)
    def test_forward_user_gen_complaint_successful_validation_email_send(self, validation, registrant):
        self.assertTrue(self._registered.forward_user_gen_complaint({}))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(SlackFailures, 'invalid_hosted_status', return_value=None)
    def test_intentionally_malicious_none(self, invalid_hosted_status, mock_db):
        self.assertFalse(self._registered.intentionally_malicious({}))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_intentionally_malicious_unsupported_type(self, invalid_abuse_type, mock_db):
        self.assertFalse(self._registered.intentionally_malicious(self.ticket_invalid_type))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(SlackFailures, 'failed_to_determine_shoppers', return_value=None)
    def test_intentionally_malicious_no_shoppers(self, failed_to_determine_shoppers, mock_db):
        self.assertFalse(self._registered.intentionally_malicious(self.ticket_no_shopper))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=False)
    def test_intentionally_malicious_already_suspended(self, throttle, mock_db):
        self.assertFalse(self._registered.intentionally_malicious(self.ticket_valid))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(SSOClient, 'lock_idp', return_value=None)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(RegisteredMailer, 'send_shopper_intentional_suspension', return_value=False)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_intentionally_malicious_failed_shopper_email_fraud_hold(self, ssl_mailer, service, crm, registered,
                                                                     slack, shoplocked, mimir, mock_db):
        self.assertFalse(self._registered.intentionally_malicious(self.ticket_fraud_hold))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(SSOClient, 'lock_idp', return_value=None)
    @patch.object(SlackFailures, 'failed_sending_revocation_email', return_value=None)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(RegisteredMailer, 'send_shopper_intentional_suspension', return_value=True)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=False)
    def test_intentionally_malicious_failed_revocation_email(self, ssl_mailer, service, crm, registered, slack,
                                                             slack_sll, shoplocked, mimir, mock_db):
        self.assertFalse(self._registered.intentionally_malicious(self.ticket_valid))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(SSOClient, 'lock_idp', return_value=None)
    @patch.object(RegisteredHandler, '_suspend_domain', return_value=True)
    @patch.object(RegisteredMailer, 'send_shopper_intentional_suspension', return_value=True)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_intentionally_malicious_no_termination_email(self, ssl_mailer, service, crm, registered, handler,
                                                          shoplocked, crmalert, mimir, mock_db):
        self.assertTrue(self._registered.intentionally_malicious(self.ticket_fraud_hold))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(SSOClient, 'lock_idp', return_value=None)
    @patch.object(RegisteredHandler, '_suspend_domain', return_value=True)
    @patch.object(RegisteredMailer, 'send_shopper_intentional_suspension', return_value=True)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_intentionally_malicious_success(self, ssl_mailer, service, crm, registered, handler, shoplocked,
                                             crmalert, mimir, mock_db):
        self.assertTrue(self._registered.intentionally_malicious(self.ticket_valid))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(SSOClient, 'lock_idp', return_value=None)
    @patch.object(RegisteredHandler, '_suspend_domain', return_value=True)
    @patch.object(RegisteredMailer, 'send_shopper_intentional_suspension', return_value=True)
    @patch.object(FraudMailer, 'send_malicious_domain_notification', return_value=None)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    @patch.object(ShopperAPI, 'get_shopper_id_from_customer_id', return_value='7890')
    def test_intentionally_malicious_no_fraud_email(self, shopper_api, ssl_mailer, service, crm, fraud, registered, handler,
                                                    shoplocked, crmalert, mimir, mock_db):
        self._registered.intentionally_malicious(self.ticket_valid_api_reseller)
        fraud.assert_not_called()

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(SSOClient, 'lock_idp', return_value=None)
    @patch.object(RegisteredHandler, '_suspend_domain', return_value=True)
    @patch.object(RegisteredMailer, 'send_shopper_intentional_suspension', return_value=True)
    @patch.object(FraudMailer, 'send_malicious_domain_notification', return_value=None)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    @patch.object(ShopperAPI, 'get_shopper_id_from_customer_id', return_value='7890')
    def test_intentionally_malicious_success_fraud_email(self, shopper_api, ssl_mailer, service, crm, fraud,
                                                         registered, handler, shoplocked, crmalert,
                                                         mimir, mock_db):
        self._registered.intentionally_malicious(self.ticket_no_hold_or_reseller)
        fraud.assert_called()
        shoplocked.assert_called_with(123456789, LockType.adminTerminated, Causes.Policy, LockTeamIDs.LtSecurity, 'Account locked for Abuse. * DO NOT UNLOCK OR REINSTATE * See http://secure.godaddy/dcuwhat2do for proper handling. Please see your direct leadership for any problems accessing this page.', None)

    @patch.object(RegisteredHandler, 'suspend', return_value=True)
    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(SSOClient, 'lock_idp', return_value=None)
    @patch.object(RegisteredHandler, '_suspend_domain', return_value=True)
    @patch.object(RegisteredMailer, 'send_shopper_intentional_suspension', return_value=True)
    @patch.object(FraudMailer, 'send_malicious_domain_notification', return_value=None)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_intentionally_malicious_hosted_same_shopper(self, ssl_mailer, service, crm, fraud,
                                                         registered, handler, shoplocked, crmalert,
                                                         mimir, mock_db, suspend):
        self._registered.intentionally_malicious(self.ticket_hosted_same_account)
        suspend.assert_not_called()
        mimir.assert_not_called()

    @patch.object(RegisteredHandler, 'suspend', return_value=True)
    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(SSOClient, 'lock_idp', return_value=None)
    @patch.object(RegisteredHandler, '_suspend_domain', return_value=True)
    @patch.object(RegisteredMailer, 'send_shopper_intentional_suspension', return_value=True)
    @patch.object(FraudMailer, 'send_malicious_domain_notification', return_value=None)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    @patch('zeus.handlers.registered_handler.datetime')
    def test_intentionally_malicious_hosted_different_shopper(self, mock_date, ssl_mailer, service, crm, fraud,
                                                              registered, handler, shoplocked, crmalert,
                                                              mimir, mock_db, suspend):
        self._registered.intentionally_malicious(self.ticket_hosted_different_account)
        suspend.assert_called()

    @patch.object(SlackFailures, 'invalid_hosted_status', return_value=None)
    def test_repeat_offender_none(self, invalid_hosted_status):
        self.assertFalse(self._registered.repeat_offender({}))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_repeat_offender_unsupported_type(self, invalid_abuse_type):
        self.assertFalse(self._registered.repeat_offender(self.ticket_invalid_type))

    @patch.object(SlackFailures, 'failed_to_determine_shoppers', return_value=None)
    def test_repeat_offender_no_shoppers(self, failed_to_determine_shoppers):
        self.assertFalse(self._registered.repeat_offender(self.ticket_no_shopper))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=False)
    def test_repeat_offender_already_suspended(self, service, crm, mimir):
        self.assertFalse(self._registered.repeat_offender(self.ticket_valid))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(RegisteredMailer, 'send_repeat_offender_suspension', return_value=False)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    def test_repeat_offender_failed_shopper_email(self, service, crm, registered, slack, mimir):
        self.assertFalse(self._registered.repeat_offender(self.ticket_valid))

    @patch.object(SlackFailures, 'failed_to_create_alert', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(RegisteredHandler, '_suspend_domain', return_value=True)
    @patch.object(RegisteredMailer, 'send_repeat_offender_suspension', return_value=True)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    def test_repeat_offender_success(self, service, crm, registered, handler, mimir, slack_infractions):
        self.assertTrue(self._registered.repeat_offender(self.ticket_valid))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(SlackFailures, 'invalid_hosted_status', return_value=None)
    def test_shopper_compromise_none(self, invalid_hosted_status, mock_db):
        self.assertFalse(self._registered.shopper_compromise({}))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_shopper_compromise_unsupported_type(self, invalid_abuse_type, mock_db):
        self.assertFalse(self._registered.shopper_compromise(self.ticket_invalid_type))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(SlackFailures, 'failed_to_determine_shoppers', return_value=None)
    def test_shopper_compromise_no_shoppers(self, failed_to_determine_shoppers, mock_db):
        self.assertFalse(self._registered.shopper_compromise(self.ticket_no_shopper))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(SSOClient, 'lock_idp', return_value=None)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=False)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_shopper_compromise_already_suspended(self, ssl_mailer, service, crm, shoplocked, mimir,
                                                  mock_db):
        self.assertFalse(self._registered.shopper_compromise(self.ticket_valid))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(SSOClient, 'lock_idp', return_value=None)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(RegisteredMailer, 'send_shopper_compromise_suspension', return_value=False)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_shopper_compromise_failed_shopper_email(self, ssl_mailer, service, crm, registered, slack,
                                                     shoplocked, mimir, mock_db):
        self.assertFalse(self._registered.shopper_compromise(self.ticket_valid))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(SSOClient, 'lock_idp', return_value=None)
    @patch.object(RegisteredHandler, '_suspend_domain', return_value=True)
    @patch.object(RegisteredMailer, 'send_shopper_compromise_suspension', return_value=True)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    def test_shopper_compromise_success(self, ssl_mailer, service, crm, registered, handler, shoplocked,
                                        mimir, mock_db):
        self.assertTrue(self._registered.shopper_compromise(self.ticket_valid))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(FraudMailer, 'send_malicious_domain_notification', return_value=None)
    @patch.object(SSOClient, 'lock_idp', return_value=None)
    @patch.object(RegisteredHandler, '_suspend_domain', return_value=True)
    @patch.object(RegisteredMailer, 'send_shopper_compromise_suspension', return_value=True)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    @patch.object(ShopperAPI, 'get_shopper_id_from_customer_id', return_value=None)
    def test_shopper_compromise_no_fraud_email(self, shopper_api, ssl_mailer, service, crm, registered, handler,
                                               shoplocked, fraud, mimir, mock_db):
        self._registered.shopper_compromise(self.ticket_valid_api_reseller)
        fraud.assert_not_called()

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(SSOClient, 'lock_idp', return_value=None)
    @patch.object(RegisteredHandler, '_suspend_domain', return_value=True)
    @patch.object(RegisteredMailer, 'send_shopper_compromise_suspension', return_value=True)
    @patch.object(FraudMailer, 'send_malicious_domain_notification', return_value=None)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    @patch.object(ShopperAPI, 'get_shopper_id_from_customer_id', return_value='7890')
    def test_shopper_compromise_success_fraud_email(self, shopper_api, ssl_mailer, service, crm, fraud, registered,
                                                    handler, shoplocked, mimir, mock_db):
        self._registered.shopper_compromise(self.ticket_no_hold_or_reseller)
        fraud.assert_called()

    @patch.object(SlackFailures, 'invalid_hosted_status', return_value=None)
    def test_suspend_none(self, invalid_hosted_status):
        self.assertFalse(self._registered.suspend({}))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_suspend_unsupported_type(self, invalid_abuse_type):
        self.assertFalse(self._registered.suspend(self.ticket_invalid_type))

    @patch.object(SlackFailures, 'failed_to_determine_shoppers', return_value=None)
    def test_suspend_no_shoppers(self, failed_to_determine_shoppers):
        self.assertFalse(self._registered.suspend(self.ticket_no_shopper))

    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=False)
    def test_suspend_already_suspended(self, service):
        self.assertFalse(self._registered.suspend(self.ticket_valid))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(RegisteredMailer, 'send_shopper_suspension', return_value=False)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    def test_suspend_failed_shopper_email(self, service, crm, mailer, slack, mimir):
        self.assertFalse(self._registered.suspend(self.ticket_valid))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(RegisteredHandler, '_suspend_domain', return_value=True)
    @patch.object(RegisteredMailer, 'send_shopper_suspension', return_value=True)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    def test_suspend_success(self, service, crm, mailer, handler, crmalert, mimir):
        self.assertTrue(self._registered.suspend(self.ticket_valid))

    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(RegisteredHandler, '_suspend_domain', return_value=True)
    @patch.object(RegisteredMailer, 'send_csam_shopper_suspension', return_value=True)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    def test_csam_suspend_success(self, service, crm, mailer, handler, crmalert, mimir):
        self.assertTrue(self._registered.suspend_csam(self.ticket_valid_child_abuse))

    @patch.object(ThrottledDomainService, 'suspend_domain', return_value=True)
    def test_suspend_domain_success(self, service):
        self.assertTrue(self._registered._suspend_domain({}, '123456789', 'reason'))

    @patch.object(SlackFailures, 'failed_domain_suspension', return_value=None)
    @patch.object(ThrottledDomainService, 'suspend_domain', return_value=False)
    def test_suspend_domain_failed(self, service, slack):
        self.assertFalse(self._registered._suspend_domain({}, '123456789', 'reason'))

    @patch.object(SlackFailures, 'failed_protected_domain_action', return_value=None)
    def test_protected_domain_action(self, slack):
        self.assertFalse(self._registered.suspend(self.ticket_protected_domain))

    @patch.object(SlackFailures, 'failed_protected_domain_action', return_value=None)
    def test_protected_domain_with_portfolio_type_action(self, slack):
        self.assertFalse(self._registered.suspend(self.ticket_protected_domain_with_portfolio_type))

    @patch.object(SlackFailures, 'failed_protected_domain_action', return_value=None)
    def test_unprotected_domain_with_portfolio_type_action(self, slack):
        self.assertFalse(self._registered.suspend(self.ticket_unprotected_domain_with_portfolio_type))

    @patch.object(SlackFailures, 'invalid_hosted_status', return_value=None)
    def test_suspend_csam_none(self, invalid_hosted_status):
        self.assertFalse(self._registered.suspend_csam({}))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_suspend_csam_unsupported_type(self, invalid_abuse_type):
        self.assertFalse(self._registered.suspend_csam(self.ticket_invalid_type))

    @patch.object(SlackFailures, 'failed_to_determine_shoppers', return_value=None)
    def test_suspend_csam_no_shoppers(self, failed_to_determine_shoppers):
        self.assertFalse(self._registered.suspend_csam(self.ticket_no_shopper))

    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=False)
    def test_suspend_csam_already_suspended(self, service):
        self.assertFalse(self._registered.suspend_csam(self.ticket_valid_child_abuse))

    @patch.object(SlackFailures, 'failed_sending_email', return_value=None)
    @patch.object(SlackFailures, 'failed_infraction_creation', return_value=None)
    @patch.object(RegisteredMailer, 'send_csam_shopper_suspension', return_value=False)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    def test_suspend_csam_failed_shopper_email(self, service, crm, mailer, slack_infraction, slack):
        self.assertFalse(self._registered.suspend_csam(self.ticket_valid_child_abuse))

    @patch.object(PhishstoryMongo, 'update_actions_sub_document', return_value=None)
    @patch.object(Mimir, 'write', return_value=None)
    @patch.object(CRMAlert, 'create_alert', return_value=None)
    @patch.object(SSOClient, 'lock_idp', return_value=None)
    @patch.object(RegisteredHandler, '_suspend_domain', return_value=True)
    @patch.object(RegisteredMailer, 'send_shopper_intentional_suspension', return_value=True)
    @patch.object(FraudMailer, 'send_malicious_domain_notification', return_value=None)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    @patch.object(ThrottledDomainService, 'can_suspend_domain', return_value=True)
    @patch.object(SSLMailer, 'send_revocation_email', return_value=True)
    @patch.object(ShopperAPI, 'get_shopper_id_from_customer_id', return_value='7890')
    def test_soft_intentionally_malicious_success_fraud_email(self, shopper_api, ssl_mailer, service, crm, fraud,
                                                              registered, handler, shoplocked, crmalert,
                                                              mimir, mock_db):
        self._registered.soft_intentionally_malicious(self.ticket_no_hold_or_reseller)
        fraud.assert_called()
        shoplocked.assert_not_called()
