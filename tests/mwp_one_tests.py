# TODO CMAPT-5272: delete this entire file
from unittest import TestCase

from mock import MagicMock, patch
from requests.exceptions import Timeout

from settings import UnitTestConfig
from zeus.events.suspension.mwp_one import MWPOne


class TestMWPOne(TestCase):
    def setUp(self):
        self._mwp_one = MWPOne(UnitTestConfig)

    @patch('requests.post', side_effect=Timeout())
    def test_suspend_fails(self, post):
        self.assertFalse(self._mwp_one.suspend('test-accountid'))

    @patch('requests.post', return_value=MagicMock(text='true', status_code=200))
    def test_suspend_success(self, post):
        self.assertTrue(self._mwp_one.suspend('test-accountid'))

    @patch('requests.post', side_effect=Timeout())
    def test_reinstate_fails(self, post):
        self.assertFalse(self._mwp_one.reinstate('test-accountid'))

    @patch('requests.post', return_value=MagicMock(text='true', status_code=200))
    def test_reinstate_success(self, post):
        self.assertTrue(self._mwp_one.reinstate('test-accountid'))
