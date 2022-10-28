from mock import MagicMock, patch
from nose.tools import assert_false, assert_true
from requests.exceptions import Timeout

from settings import UnitTestConfig
from zeus.events.suspension.nes_helper import NESHelper


class TestNESHelper:
    @classmethod
    def setup(cls):
        cls._nes_helper = NESHelper(UnitTestConfig)

    # TODO LKM: also mock 'poll for entitlement status' function for the suspend / reinstate tests
    @patch('requests.post', side_effect=Timeout())
    def test_suspend_exception(self, post):
        response = self._nes_helper.suspend('test-accountid', 'test-customerid')
        # Verify we got a string message back and it contains the word 'exception'
        assert_in('exception', response)

    @patch('requests.post', return_value=MagicMock(text='true', status_code=204))
    def test_suspend_success(self, post):
        assert_true(self._nes_helper.suspend('test-accountid', 'test-customerid'))

    @patch('requests.post', side_effect=Timeout())
    def test_reinstate_fails(self, post):
        assert_false(self._nes_helper.reinstate('test-accountid'))

    @patch('requests.post', return_value=MagicMock(text='true', status_code=204))
    def test_reinstate_success(self, post):
        assert_true(self._nes_helper.reinstate('test-accountid'))

    # TODO LKM: also add tests for:
    #  - non-exception failure response in suspend / reinstate
    #  - suspend / reinstate where poll for entitlement status returns an error / exception
    #  - '_check_entitlement_status' function: sucess, fail due to error, fail due to exception
    #  - '_poll_for_entitlement_status' function: fail due to error, fail due to exception, success...
    #     can we somehow test it is called multiple times if the check entitlement status is mocked to return the wrong status??