from mock import MagicMock, patch
from nose.tools import assert_true, assert_in, assert_equal
from requests.exceptions import Timeout

from settings import UnitTestConfig
from zeus.events.suspension.nes_helper import NESHelper


class TestNESHelper:
    @classmethod
    def setup(cls):
        cls._nes_helper = NESHelper(UnitTestConfig)

    @patch('requests.post', side_effect=Timeout())
    @patch('zeus.events.suspension.nes_helper.NESHelper.wait_for_entitlement_status', return_value=True)
    def test_suspend_exception(self, post, wait_for_entitlement_status):
        response = self._nes_helper.suspend('test-accountid', 'test-customerid')
        # Verify the response contains the word 'exception'
        assert_in('exception', response)

    @patch('requests.post', return_value=MagicMock(text='true', status_code=204))
    @patch('zeus.events.suspension.nes_helper.NESHelper.wait_for_entitlement_status', return_value=True)
    def test_suspend_success(self, post, wait_for_entitlement_status):
        assert_true(self._nes_helper.suspend('test-accountid', 'test-customerid'))

    @patch('requests.post', return_value=MagicMock(text='failure message', status_code=404))
    @patch('zeus.events.suspension.nes_helper.NESHelper.wait_for_entitlement_status', return_value=True)
    def test_suspend_fail(self, post, wait_for_entitlement_status):
        response = self._nes_helper.suspend('test-accountid', 'test-customerid')
        # Verify the response contains the stautus and failure message
        assert_in('failure message', response)
        assert_in('404', response)

    @patch('requests.post', return_value=MagicMock(status_code=204))
    @patch('zeus.events.suspension.nes_helper.NESHelper.wait_for_entitlement_status', return_value='Entitlement error message')
    def test_suspend_entitlement_error(self, post, wait_for_entitlement_status):
        response = self._nes_helper.suspend('test-accountid', 'test-entitlementid')
        # Verify the response contains the entitlement error
        assert_equal('Entitlement error message', response)

    @patch('requests.post', side_effect=Timeout())
    @patch('zeus.events.suspension.nes_helper.NESHelper.wait_for_entitlement_status', return_value=True)
    def test_reinstate_exception(self, post, wait_for_entitlement_status):
        response = self._nes_helper.reinstate('test-accountid', 'test-customerid')
        assert_in('exception', response)

    @patch('requests.post', return_value=MagicMock(text='true', status_code=204))
    @patch('zeus.events.suspension.nes_helper.NESHelper.wait_for_entitlement_status', return_value=True)
    def test_reinstate_success(self, post, wait_for_entitlement_status):
        assert_true(self._nes_helper.reinstate('test-accountid', 'test-customerid'))

    @patch('requests.post', return_value=MagicMock(text='failure message', status_code=404))
    @patch('zeus.events.suspension.nes_helper.NESHelper.wait_for_entitlement_status', return_value=True)
    def test_reinstate_fail(self, post, wait_for_entitlement_status):
        response = self._nes_helper.reinstate('test-accountid', 'test-customerid')
        assert_in('failure message', response)
        assert_in('404', response)

    @patch('requests.post', return_value=MagicMock(status_code=204))
    @patch('zeus.events.suspension.nes_helper.NESHelper.wait_for_entitlement_status', return_value='Entitlement error message')
    def test_reinstate_entitlement_error(self, post, wait_for_entitlement_status):
        response = self._nes_helper.suspend('test-accountid', 'test-entitlementid')
        # Verify the response contains the entitlement error
        assert_equal('Entitlement error message', response)

    @patch('requests.post', return_value=MagicMock(status_code=200, text='{status: SUSPENDED}'))
    def test_entitlement_status_sucess(self, post):
        assert_true(self._nes_helper.wait_for_entitlement_status('test-accountid', 'test-customerid', 'SUSPENDED'))

    @patch('requests.get', return_value=MagicMock(status_code=404, text='failure message'))
    def test_entitlement_status_fail(self, post):
        response = self._nes_helper.wait_for_entitlement_status('test-accountid', 'test-customerid', 'SUSPENDED')
        # Verify the response contains the status code and error message
        assert_in('404', response)
        assert_in('failure message', response)

    @patch('requests.get', side_effect=Timeout())
    def test_entitlement_status_exception(self, post):
        response = self._nes_helper.wait_for_entitlement_status('test-accountid', 'test-customerid', 'SUSPENDED')
        # Verify the response contains the word 'exception'
        assert_in('exception', response)

    # # TODO LKM: figure out what to do for this test
    # @patch('requests.get', return_value=MagicMock(status_code=200, text='{status: ACTIVE'))
    # def test_entitlement_status_mismatch(self, post):
    #     response = self._nes_helper.wait_for_entitlement_status('test-accountid', 'test-customerid', 'SUSPENDED')
    #     # soooo.....right now, this will just run forever; figure out timeout and then verify this takes the full timeout???
