# TODO CMAPT-5272: delete this entire file
from unittest import TestCase

from mock import MagicMock, patch
from requests.exceptions import Timeout

from settings import UnitTestConfig
from zeus.events.suspension.diablo import Diablo


class TestDiablo(TestCase):
    def setUp(self):
        self._diablo = Diablo(UnitTestConfig)

    @patch('requests.post', side_effect=Timeout())
    def test_suspend_fails(self, post):
        self.assertFalse(self._diablo.suspend('test-guid'))

    @patch('requests.post', return_value=MagicMock(status_code=200))
    def test_suspend_success(self, post):
        self.assertTrue(self._diablo.suspend('test-guid'))

    @patch('requests.post', side_effect=Timeout())
    def test_reinstate_fails(self, post):
        self.assertFalse(self._diablo.reinstate('test-guid'))

    @patch('requests.post', return_value=MagicMock(status_code=200))
    def test_reinstate_success(self, post):
        self.assertTrue(self._diablo.reinstate('test-guid'))
