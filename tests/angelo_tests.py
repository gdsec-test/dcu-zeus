from mock import patch, MagicMock
from nose.tools import assert_false, assert_true
from requests.exceptions import Timeout

from settings import TestingConfig
from zeus.events.suspension.angelo import Angelo


class TestAngelo:
    @classmethod
    def setup(cls):
        cls._angelo = Angelo(TestingConfig)

    @patch('requests.post', side_effect=Timeout())
    def test_suspend_fails(self, post):
        data = {'data': {'domainQuery': {'host': {'shopperId': 'test-id'}}}}
        assert_false(self._angelo.suspend('test-guid', data))

    @patch('requests.post', return_value=MagicMock(status_code=200))
    def test_suspend_success(self, post):
        data = {'data': {'domainQuery': {'host': {'shopperId': 'test-id'}}}}
        assert_true(self._angelo.suspend('test-guid', data))

    @patch('requests.post', side_effect=Timeout())
    def test_reinstate_fails(self, post):
        data = {'data': {'domainQuery': {'host': {'shopperId': 'test-id'}}}}
        assert_false(self._angelo.reinstate('test-guid', data))

    @patch('requests.post', return_value=MagicMock(status_code=200))
    def test_reinstate_success(self, post):
        data = {'data': {'domainQuery': {'host': {'shopperId': 'test-id'}}}}
        assert_true(self._angelo.reinstate('test-guid', data))
