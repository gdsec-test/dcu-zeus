
from nose.tools import assert_false
from mock import patch

from zeus.handlers.registered_handler import RegisteredHandler
from zeus.utils.slack import SlackFailures

from settings import TestingConfig


class TestRegisteredHandler:

    @classmethod
    def setup(cls):
        cls._registered = RegisteredHandler(TestingConfig)

    def test_process_invalid_mapping(self):
        assert_false(self._registered.process({}, 'invalid-request'))

    def test_customer_warning_none(self):
        assert_false(self._registered.customer_warning({}))

    def test_customer_warning_unsupported_type(self):
        data = {'hosted_status': 'REGISTERED'}
        assert_false(self._registered.customer_warning(data))

    def test_customer_warning_no_shoppers(self):
        data = {'hosted_status': 'REGISTERED', 'type': 'PHISHING'}
        assert_false(self._registered.customer_warning(data))

    def test_intentionally_malicious_none(self):
        assert_false(self._registered.intentionally_malicious({}))

    def test_intentionally_malicious_unsupported_type(self):
        data = {'hosted_status': 'REGISTERED'}
        assert_false(self._registered.intentionally_malicious(data))

    @patch.object(SlackFailures, 'failed_to_determine_shoppers')
    def test_intentionally_malicious_no_shoppers(self, failed_to_determine_shoppers):
        failed_to_determine_shoppers.return_value = None
        data = {'hosted_status': 'REGISTERED', 'type': 'PHISHING'}
        assert_false(self._registered.intentionally_malicious(data))

    def test_suspend_none(self):
        assert_false(self._registered.suspend({}))

    def test_suspend_unsupported_type(self):
        data = {'hosted_status': 'REGISTERED'}
        assert_false(self._registered.suspend(data))

    @patch.object(SlackFailures, 'failed_to_determine_shoppers')
    def test_suspend_no_shoppers(self, failed_to_determine_shoppers):
        failed_to_determine_shoppers.return_value = None
        data = {'hosted_status': 'REGISTERED', 'type': 'PHISHING'}
        assert_false(self._registered.suspend(data))

    def test_suspend_domain(self):
        pass
