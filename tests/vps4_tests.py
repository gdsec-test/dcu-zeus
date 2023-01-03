# TODO CMAPT-5272: delete this entire file
from unittest import TestCase

import requests
from mock import MagicMock, patch
from requests.exceptions import Timeout

from settings import UnitTestConfig
from zeus.events.suspension.vps4 import VPS4


class TestVPS4(TestCase):
    def setUp(self):
        self._vps4 = VPS4(UnitTestConfig)

    @patch('requests.get', side_effect=Timeout())
    @patch('requests.post', return_value=MagicMock(text='true'))
    @patch.object(VPS4, '_get_jwt', return_value='fake-jwt')
    def test_suspend_fails(self, mock_vps, post, get):
        self.assertFalse(self._vps4.suspend('test-accountid', {}))

    @patch.object(VPS4, '_retrieve_credits', return_value={'productId': 1, 'abuseSuspendedFlagSet': True})
    @patch.object(requests, 'post', return_value=MagicMock(text='true', status_code=200))
    @patch.object(VPS4, '_get_jwt', return_value='fake-jwt')
    def test_suspend_success(self, mock_vps, post, mock_credits):
        self.assertTrue(self._vps4.suspend('test-accountid', {}))

    @patch.object(VPS4, '_retrieve_credits', return_value={'productId': 1, 'abuseSuspendedFlagSet': True})
    @patch.object(requests, 'post', return_value=MagicMock(text='true', status_code=200))
    @patch.object(VPS4, '_get_jwt', return_value='fake-jwt')
    def test_suspend_known_dc(self, mock_vps, post, mock_credits):
        self.assertTrue(self._vps4.suspend('test-accountid', {'data': {'domainQuery': {'host': {'dataCenter': 'SIN2'}}}}))
