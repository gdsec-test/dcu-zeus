import os

from mock import MagicMock, patch
from requests.exceptions import Timeout

from settings import UnitTestConfig
from unittest import TestCase
from zeus.events.suspension.nes_helper import NESHelper


class TestNESHelper(TestCase):
    HOSTED_DIABLO_DATA = {'hosted_status': 'HOSTED', 'data': {'domainQuery': {'host': {'product': 'diablo'}}}}

    def setUp(self):
        NESHelper._get_jwt = MagicMock(return_value='testJWT')
        self._nes_helper = NESHelper(UnitTestConfig())

    @patch('zeus.events.suspension.nes_helper.requests.post', side_effect=Timeout())
    def test_suspend_exception(self, post):
        self.assertFalse(self._nes_helper.suspend('test-accountid', 'test-customerid'))

    @patch('zeus.events.suspension.nes_helper.requests.post', return_value=MagicMock(status_code=204))
    def test_suspend_success(self, post):
        self.assertTrue(self._nes_helper.suspend('test-accountid', 'test-customerid'))

    @patch('zeus.events.suspension.nes_helper.requests.post', return_value=MagicMock(status_code=404))
    def test_suspend_fail(self, post):
        self.assertFalse(self._nes_helper.suspend('test-accountid', 'test-customerid'))

    @patch('zeus.events.suspension.nes_helper.requests.post', return_value=MagicMock(status_code=204))
    @patch('zeus.events.suspension.nes_helper.NESHelper._get_entitlement_status', return_value='SUSPENDED')
    def test_suspend_already_suspended(self, post, get_entitlement_status):
        # Verify suspension returns true AND that post was not called
        self.assertTrue(self._nes_helper.suspend('test-accountid', 'test-customerid'))
        self.assertFalse(post.called)

    @patch('zeus.events.suspension.nes_helper.requests.post', side_effect=Timeout())
    def test_reinstate_exception(self, post):
        self.assertFalse(self._nes_helper.reinstate('test-accountid', 'test-customerid'))

    @patch('zeus.events.suspension.nes_helper.requests.post', return_value=MagicMock(status_code=204))
    def test_reinstate_success(self, post):
        self.assertTrue(self._nes_helper.reinstate('test-accountid', 'test-customerid'))

    @patch('zeus.events.suspension.nes_helper.requests.post', return_value=MagicMock(status_code=404))
    def test_reinstate_fail(self, post):
        self.assertFalse(self._nes_helper.reinstate('test-accountid', 'test-customerid'))

    @patch('zeus.events.suspension.nes_helper.requests.post', return_value=MagicMock(status_code=204))
    @patch('zeus.events.suspension.nes_helper.NESHelper._get_entitlement_status', return_value='ACTIVE')
    def test_reinstate_already_active(self, post, get_entitlement_status):
        # Verify suspension returns true AND that post was not called
        self.assertTrue(self._nes_helper.reinstate('test-accountid', 'test-customerid'))
        self.assertFalse(post.called)

    @patch('zeus.events.suspension.nes_helper.requests.get', return_value=MagicMock(status_code=200, json=MagicMock(return_value={'status': 'SUSPENDED'})))
    def test_entitlement_status_success(self, get):
        status = self._nes_helper._get_entitlement_status('test-accountid', 'test-customerid')
        self.assertEqual('SUSPENDED', status)
        get.assert_called_with(
            'https://entitlements-ext.cp.api.prod.godaddy.com/v2/customers/test-customerid/entitlements/test-accountid',
            headers={'Content-Type': 'application/json', 'x-app-key': 'zeus', 'Authorization': 'sso-jwt testJWT'},
            timeout=30
        )

    # @patch('zeus.events.suspension.nes_helper.requests.get', return_value=MagicMock(status_code=404))
    # def test_entitlement_status_error(self, get):
    #     self.assertEqual('Failed to get entitlement status', self._nes_helper._check_entitlement_status('test-accountid', 'test-customerid'))

    # @patch('zeus.events.suspension.nes_helper.requests.get', sideEffect=Timeout())
    # def test_entitlement_status_exception(self, get):
    #     self.assertEqual('Exception thrown while trying to get entitlement status', self._nes_helper._check_entitlement_status('test-accountid', 'test-customerid'))

    @patch.dict(os.environ, {"DIABLO_USE_NES": "False", "ALL_USE_NES": "False"})
    def test_get_use_nes_none(self):
        self.assertFalse(self._nes_helper.get_use_nes({'hosted_status': 'HOSTED', 'data': {'domainQuery': {'host': {'product': 'diablo'}}}}))

    @patch.dict(os.environ, {"DIABLO_USE_NES": "False", "ALL_USE_NES": "False", "VERTIGO_USE_NES": "True"})
    def test_get_use_nes_product_false(self):
        self.assertFalse(self._nes_helper.get_use_nes({'hosted_status': 'HOSTED', 'data': {'domainQuery': {'host': {'product': 'diablo'}}}}))

    @patch.dict(os.environ, {'DIABLO_USE_NES': 'True'})
    @patch.dict(os.environ, {'ALL_USE_NES': 'False'})
    def test_get_use_nes_product_true(self):
        print(os.environ)
        self.assertTrue(self._nes_helper.get_use_nes(self.HOSTED_DIABLO_DATA))

    @patch.dict(os.environ, {"DIABLO_USE_NES": "False", "ALL_USE_NES": "True"})
    def test_get_use_nes_all_true(self):
        self.assertTrue(self._nes_helper.get_use_nes({'hosted_status': 'HOSTED', 'data': {'domainQuery': {'host': {'product': 'diablo'}}}}))

    def test_get_use_nes_not_hosted(self):
        self.assertFalse(self._nes_helper.get_use_nes({'hosted_status': 'REGISTERED'}))

    def test_get_use_nes_no_product(self):
        self.assertFalse(self._nes_helper.get_use_nes({'hosted_status': 'HOSTED'}))

    def test_set_nes_state(self):
        self._nes_helper.set_nes_state('UP')
        self.assertTrue(self._nes_helper.get_nes_state())
