from unittest import TestCase

from mock import patch

from settings import UnitTestConfig
from zeus.events.email.fraud_mailer import FraudMailer
from zeus.handlers.fraud_handler import FraudHandler


class TestFraudHandler(TestCase):
    def setUp(self):
        self._fraud = FraudHandler(UnitTestConfig)

    @patch.object(FraudMailer, 'send_new_domain_notification', return_value=False)
    def test_new_domain_failure(self, new_domain):
        self.assertFalse(self._fraud.new_domain({}))

    @patch.object(FraudMailer, 'send_new_domain_notification', return_value=True)
    def test_new_domain_success(self, new_domain):
        self.assertTrue(self._fraud.new_domain({}))

    @patch.object(FraudMailer, 'send_new_shopper_notification', return_value=False)
    def test_new_shopper_failure(self, new_shopper):
        self.assertFalse(self._fraud.new_shopper({}))

    @patch.object(FraudMailer, 'send_new_shopper_notification', return_value=True)
    def test_new_shopper_success(self, new_shopper):
        self.assertTrue(self._fraud.new_shopper({}))

    @patch.object(FraudMailer, 'send_new_hosting_account_notification', return_value=False)
    def test_new_hosting_account_no_shopper(self, new_hosting_account):
        self.assertFalse(self._fraud.new_hosting_account({}))

    @patch.object(FraudMailer, 'send_new_hosting_account_notification', return_value=False)
    def test_new_hosting_account_failure(self, new_hosting_account):
        data = {'data': {'domainQuery': {'host': {'shopperId': 'test-id'}}}}
        self.assertFalse(self._fraud.new_hosting_account(data))

    @patch.object(FraudMailer, 'send_new_hosting_account_notification', return_value=True)
    def test_new_hosting_account_success(self, new_hosting_account):
        data = {'data': {'domainQuery': {'host': {'shopperId': 'test-id'}}}}
        self.assertTrue(self._fraud.new_hosting_account(data))
