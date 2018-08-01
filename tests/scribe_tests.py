from mock import patch
from nose.tools import assert_false, assert_true

from settings import TestingConfig
from zeus.events.support_tools.crm import ThrottledCRM
from zeus.events.support_tools.netvio import ThrottledNetvio
from zeus.utils.scribe import HostedScribe
from zeus.utils.slack import SlackFailures


class TestHostedScribe:
    @classmethod
    def setup(cls):
        cls._scribe = HostedScribe(TestingConfig)

    @patch.object(SlackFailures, 'failed_netvio_creation', return_value=None)
    @patch.object(ThrottledNetvio, 'create_ticket', return_value=False)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    def test_customer_warning_fail(self, notate_crm_account, create_ticket, failed_netvio_creation):
        actual = self._scribe.customer_warning('test-ticket', 'test-guid', 'url', 'report-type', 'shopper-id')
        assert_false(actual)

    @patch.object(ThrottledNetvio, 'create_ticket', return_value=True)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    def test_customer_warning_success(self, notate_crm_account, create_ticket):
        actual = self._scribe.customer_warning('test-ticket', 'test-guid', 'url', 'report-type', 'shopper-id')
        assert_true(actual)

    @patch.object(SlackFailures, 'failed_netvio_creation', return_value=None)
    @patch.object(ThrottledNetvio, 'create_ticket', return_value=False)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    def test_suspension_fail(self, notate_crm_account, create_ticket, failed_netvio_creation):
        actual = self._scribe.suspension('test-ticket', 'test-guid', 'url', 'report-type', 'shopper-id')
        assert_false(actual)

    @patch.object(ThrottledNetvio, 'create_ticket', return_value=True)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    def test_suspension_success(self, notate_crm_account, create_ticket):
        actual = self._scribe.suspension('test-ticket', 'test-guid', 'url', 'report-type', 'shopper-id')
        assert_true(actual)

    @patch.object(SlackFailures, 'failed_netvio_creation', return_value=None)
    @patch.object(ThrottledNetvio, 'create_ticket', return_value=False)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    def test_intentionally_malicious_fail(self, notate_crm_account, create_ticket, failed_netvio_creation):
        actual = self._scribe.intentionally_malicious('test-ticket', 'test-guid', 'url', 'report-type', 'shopper-id')
        assert_false(actual)

    @patch.object(ThrottledNetvio, 'create_ticket', return_value=True)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    def test_intentionally_malicious_success(self, notate_crm_account, create_ticket):
        actual = self._scribe.intentionally_malicious('test-ticket', 'test-guid', 'url', 'report-type', 'shopper-id')
        assert_true(actual)

    @patch.object(SlackFailures, 'failed_netvio_creation', return_value=None)
    @patch.object(ThrottledNetvio, 'create_ticket', return_value=False)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    def test_content_removed_fail(self, notate_crm_account, create_ticket, failed_netvio_creation):
        actual = self._scribe.content_removed('test-ticket', 'test-guid', 'url', 'report-type', 'shopper-id', 'removed')
        assert_false(actual)

    @patch.object(ThrottledNetvio, 'create_ticket', return_value=True)
    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    def test_content_removed_success(self, notate_crm_account, create_ticket):
        actual = self._scribe.content_removed('test-ticket', 'test-guid', 'url', 'report-type', 'shopper-id', 'removed')
        assert_true(actual)
