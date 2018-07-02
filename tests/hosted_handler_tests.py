from nose.tools import assert_false, assert_equal
from mock import patch

from zeus.handlers.hosted_handler import HostedHandler
from zeus.utils.slack import SlackFailures

from settings import TestingConfig


class TestHostedHandler:

    @classmethod
    def setup(cls):
        cls._hosted = HostedHandler(TestingConfig)

    def test_process_invalid_mapping(self):
        assert_false(self._hosted.process({}, 'invalid-request'))

    @patch.object(SlackFailures, 'invalid_abuse_type')
    def test_validate_required_args_unsupported_type(self, invalid_abuse_type):
        invalid_abuse_type.return_value = None
        data = {}
        assert_equal((None, None, None), self._hosted._validate_required_args(data))

    @patch.object(SlackFailures, 'failed_to_determine_guid')
    def test_validate_required_args_no_guid(self, failed_to_determine_guid):
        failed_to_determine_guid.return_value = None
        data = {'type': 'PHISHING'}
        assert_equal((None, None, None), self._hosted._validate_required_args(data))

    @patch.object(SlackFailures, 'failed_to_determine_shoppers')
    def test_validate_required_args_no_shopper(self, failed_to_determine_shoppers):
        failed_to_determine_shoppers.return_value = None
        data = {'type': 'PHISHING', 'data': {'domainQuery': {'host': {'guid': 'test-guid'}}}}
        assert_equal((None, None, None), self._hosted._validate_required_args(data))

    def test_validate_required(self):
        data = {'type': 'PHISHING', 'data': {'domainQuery': {'host': {'guid': 'test-guid', 'shopperId': 'test-id'}}}}
        assert_equal(('PHISHING', 'test-guid', 'test-id'), self._hosted._validate_required_args(data))

    @patch.object(SlackFailures, 'invalid_abuse_type')
    def test_customer_warning_none(self, invalid_abuse_type):
        invalid_abuse_type.return_value = None
        assert_false(self._hosted.customer_warning({}))

    @patch.object(SlackFailures, 'invalid_abuse_type')
    def test_intentionally_malicious_none(self, invalid_abuse_type):
        invalid_abuse_type.return_value = None
        assert_false(self._hosted.intentionally_malicious({}))

    @patch.object(SlackFailures, 'invalid_abuse_type')
    def test_suspend_none(self, invalid_abuse_type):
        invalid_abuse_type.return_value = None
        assert_false(self._hosted.suspend({}))
