# TODO CMAPT-5272: delete this entire file
from unittest import TestCase

from mock import MagicMock, patch
from requests.exceptions import Timeout

from settings import UnitTestConfig
from zeus.events.suspension.angelo import Angelo


class TestAngelo(TestCase):

    def setUp(self):
        self._angelo = Angelo(UnitTestConfig)

    @patch('requests.post', side_effect=Timeout())
    def test_suspend_fails(self, post):
        data = {'data': {'domainQuery': {'host': {'shopperId': 'test-id'}}}}
        self.assertFalse(self._angelo.suspend('test-guid', data))

    @patch('requests.post', return_value=MagicMock(status_code=200))
    def test_suspend_success(self, post):
        data = {'data': {'domainQuery': {'host': {'shopperId': 'test-id'}}}}
        self.assertTrue(self._angelo.suspend('test-guid', data))

    @patch('requests.post', side_effect=Timeout())
    def test_reinstate_fails(self, post):
        data = {'data': {'domainQuery': {'host': {'shopperId': 'test-id'}}}}
        self.assertFalse(self._angelo.reinstate('test-guid', data))

    @patch('requests.post', return_value=MagicMock(status_code=200))
    def test_reinstate_success(self, post):
        data = {'data': {'domainQuery': {'host': {'shopperId': 'test-id'}}}}
        self.assertTrue(self._angelo.reinstate('test-guid', data))
