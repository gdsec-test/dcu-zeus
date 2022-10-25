from mock import MagicMock, patch
from nose.tools import assert_false, assert_true
from requests.exceptions import Timeout

from settings import UnitTestConfig
from zeus.events.suspension.diablo import Diablo


class TestDiablo:
    @classmethod
    def setup(cls):
        cls._diablo = Diablo(UnitTestConfig)

    @patch('requests.post', side_effect=Timeout())
    def test_suspend_fails(self, post):
        assert_false(self._diablo.suspend('test-guid'))

    @patch('requests.post', return_value=MagicMock(status_code=200))
    def test_suspend_success(self, post):
        assert_true(self._diablo.suspend('test-guid'))

    @patch('requests.post', side_effect=Timeout())
    def test_reinstate_fails(self, post):
        assert_false(self._diablo.reinstate('test-guid'))

    @patch('requests.post', return_value=MagicMock(status_code=200))
    def test_reinstate_success(self, post):
        assert_true(self._diablo.reinstate('test-guid'))
