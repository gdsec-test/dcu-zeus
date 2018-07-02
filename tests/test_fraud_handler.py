from mock import patch
from nose.tools import assert_false, assert_true

from settings import TestingConfig
from zeus.events.email.fraud_mailer import FraudMailer
from zeus.handlers.fraud_handler import FraudHandler


class TestFraudHandler:
    @classmethod
    def setup(cls):
        cls._fraud = FraudHandler(TestingConfig)

    @patch.object(FraudMailer, 'send_new_domain_notification')
    def test_new_domain_failure(self, new_domain):
        new_domain.return_value = False
        assert_false(self._fraud.new_domain({}))

    @patch.object(FraudMailer, 'send_new_domain_notification')
    def test_new_domain_success(self, new_domain):
        new_domain.return_value = True
        assert_true(self._fraud.new_domain({}))

    @patch.object(FraudMailer, 'send_new_shopper_notification')
    def test_new_shopper_failure(self, new_shopper):
        new_shopper.return_value = False
        assert_false(self._fraud.new_shopper({}))

    @patch.object(FraudMailer, 'send_new_shopper_notification')
    def test_new_shopper_success(self, new_shopper):
        new_shopper.return_value = True
        assert_true(self._fraud.new_shopper({}))

    @patch.object(FraudMailer, 'send_new_hosting_account_notification')
    def test_new_hosting_account_no_shopper(self, new_hosting_account):
        new_hosting_account.return_value = False
        assert_false(self._fraud.new_hosting_account({}))

    @patch.object(FraudMailer, 'send_new_hosting_account_notification')
    def test_new_hosting_account_failure(self, new_hosting_account):
        new_hosting_account.return_value = False
        data = {'data': {'domainQuery': {'host': {'shopperId': 'test-id'}}}}
        assert_false(self._fraud.new_hosting_account(data))

    @patch.object(FraudMailer, 'send_new_hosting_account_notification')
    def test_new_hosting_account_success(self, new_hosting_account):
        new_hosting_account.return_value = True
        data = {'data': {'domainQuery': {'host': {'shopperId': 'test-id'}}}}
        assert_true(self._fraud.new_hosting_account(data))
