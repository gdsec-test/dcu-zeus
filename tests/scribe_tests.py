from unittest import TestCase

from mock import patch

from settings import UnitTestConfig
from zeus.events.support_tools.crm import ThrottledCRM
from zeus.utils.scribe import HostedScribe


class TestHostedScribe(TestCase):
    def setUp(self):
        self._scribe = HostedScribe(UnitTestConfig)

    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    def test_customer_warning_success(self, notate_crm_account):
        self.assertTrue(self._scribe.customer_warning('test-ticket', 'test-guid', 'url', 'report-type', 'shopper-id'))

    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    def test_suspension_success(self, notate_crm_account):
        self.assertTrue(self._scribe.suspension('test-ticket', 'test-guid', 'url', 'report-type', 'shopper-id'))

    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    def test_intentionally_malicious_success(self, notate_crm_account):
        self.assertTrue(self._scribe.intentionally_malicious('test-ticket', 'test-guid', 'url', 'report-type', 'shopper-id'))

    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    def test_shopper_compromise_success(self, notate_crm_account):
        self.assertTrue(self._scribe.shopper_compromise('test-ticket', 'test-guid', 'url', 'report-type', 'shopper-id'))

    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    def test_content_removed_success(self, notate_crm_account):
        self.assertTrue(self._scribe.content_removed('test-ticket', 'test-guid', 'url', 'report-type', 'shopper-id'))

    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    def test_repeat_offender_success(self, notate_crm_account):
        self.assertTrue(self._scribe.repeat_offender('test-ticket', 'test-guid', 'url', 'report-type', 'shopper-id'))

    @patch.object(ThrottledCRM, 'notate_crm_account', return_value=None)
    def test_extensive_compromise_success(self, notate_crm_account):
        self.assertTrue(self._scribe.extensive_compromise('test-ticket', 'test-guid', 'url', 'report-type', 'shopper-id'))
