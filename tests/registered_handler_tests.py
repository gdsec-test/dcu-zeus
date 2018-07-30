from mock import patch
from nose.tools import assert_false

from settings import TestingConfig
from zeus.handlers.registered_handler import RegisteredHandler
from zeus.utils.slack import SlackFailures


class TestRegisteredHandler:
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
        data = {'hosted_status': 'REGISTERED'}
        assert_false(self._registered.customer_warning(data))

    @patch.object(SlackFailures, 'failed_to_determine_shoppers', return_value=None)
    def test_customer_warning_no_shoppers(self, failed_to_determine_shoppers):
        data = {'hosted_status': 'REGISTERED', 'type': 'PHISHING'}
        assert_false(self._registered.customer_warning(data))

    @patch.object(SlackFailures, 'invalid_hosted_status', return_value=None)
    def test_intentionally_malicious_none(self, invalid_hosted_status):
        assert_false(self._registered.intentionally_malicious({}))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_intentionally_malicious_unsupported_type(self, invalid_abuse_type):
        data = {'hosted_status': 'REGISTERED'}
        assert_false(self._registered.intentionally_malicious(data))

    @patch.object(SlackFailures, 'failed_to_determine_shoppers', return_value=None)
    def test_intentionally_malicious_no_shoppers(self, failed_to_determine_shoppers):
        data = {'hosted_status': 'REGISTERED', 'type': 'PHISHING'}
        assert_false(self._registered.intentionally_malicious(data))

    @patch.object(SlackFailures, 'invalid_hosted_status', return_value=None)
    def test_suspend_none(self, invalid_hosted_status):
        assert_false(self._registered.suspend({}))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_suspend_unsupported_type(self, invalid_abuse_type):
        data = {'hosted_status': 'REGISTERED'}
        assert_false(self._registered.suspend(data))

    @patch.object(SlackFailures, 'failed_to_determine_shoppers', return_value=None)
    def test_suspend_no_shoppers(self, failed_to_determine_shoppers):
        data = {'hosted_status': 'REGISTERED', 'type': 'PHISHING'}
        assert_false(self._registered.suspend(data))

    def test_suspend_domain(self):
        pass
