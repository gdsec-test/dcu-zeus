# TODO CMAPT-5272: delete this entire file
from unittest import TestCase

from mock import MagicMock, patch
from requests.exceptions import Timeout

from settings import UnitTestConfig
from zeus.events.suspension.mwp_one import MWPOne


class TestMWPOne(TestCase):
    def setUp(self):
        self._mwp_one = MWPOne(UnitTestConfig)
        self._mwp_one._get_shopper_jwt = MagicMock()
        self._mwp_one._get_shopper_jwt.return_value = 'jwt1'

    @patch('requests.post', side_effect=Timeout())
    def test_suspend_fails(self, post):
        self.assertFalse(self._mwp_one.suspend('test-accountid', data={'shopperid': 'sid1'}))

    @patch('requests.post')
    def test_suspend_success(self, mock_post):
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {'successful': True}
        mock_post.return_value = mock_response
        self.assertTrue(self._mwp_one.suspend('test-accountid', data={'shopperid': 'sid1'}))

    @patch('requests.post', side_effect=Timeout())
    def test_reinstate_fails(self, post):
        self.assertFalse(self._mwp_one.reinstate('test-accountid', data={'shopperid': 'sid1'}))

    @patch('requests.post')
    def test_reinstate_success(self, mock_post):
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {'successful': True}
        mock_post.return_value = mock_response
        self.assertTrue(self._mwp_one.reinstate('test-accountid', data={'shopperid': 'sid1'}))
