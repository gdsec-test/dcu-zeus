from mock import patch, MagicMock
from nose.tools import assert_false, assert_true
from requests.exceptions import Timeout

from settings import TestingConfig
from zeus.events.suspension.mwp_one import MWPOne


class TestMWPOne:
    @classmethod
    def setup(cls):
        cls._mwp_one = MWPOne(TestingConfig)

    @patch('requests.post', side_effect=Timeout())
    def test_suspend_fails(self, post):
        assert_false(self._mwp_one.suspend('test-accountid'))

    @patch('requests.post', return_value=MagicMock(text='true'))
    def test_suspend_success(self, post):
        assert_true(self._mwp_one.suspend('test-accountid'))

    @patch('requests.post', side_effect=Timeout())
    def test_reinstate_fails(self, post):
        assert_false(self._mwp_one.reinstate('test-accountid'))

    @patch('requests.post', return_value=MagicMock(text='true'))
    def test_reinstate_success(self, post):
        assert_true(self._mwp_one.reinstate('test-accountid'))
