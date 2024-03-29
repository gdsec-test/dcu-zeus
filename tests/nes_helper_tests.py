import os
from datetime import timedelta
from json import loads
from unittest import TestCase

from mock import MagicMock, patch
from requests.exceptions import Timeout

from settings import UnitTestConfig
from zeus.events.suspension.nes_helper import NESHelper


class TestNESHelper(TestCase):
    HOSTED_DIABLO_DATA = {'hosted_status': 'HOSTED', 'data': {'domainQuery': {'host': {'product': 'diablo'}}}}
    with open(f'{os.path.dirname(os.path.realpath(__file__))}/sub-shim-json.json', 'r') as f:
        SUBSCRIPTION_DATA = loads(f.read())

    def setUp(self):
        NESHelper._get_jwt = MagicMock(return_value='testJWT')
        self._nes_helper = NESHelper(UnitTestConfig())

    @patch('zeus.events.suspension.nes_helper.Redis.setex')
    @patch('zeus.events.suspension.nes_helper.requests.get', return_value=MagicMock(status_code=200, json=MagicMock(return_value={'status': 'ACTIVE'})))
    @patch('zeus.events.suspension.nes_helper.requests.post', side_effect=Timeout())
    def test_suspend_exception(self, post, get, setex):
        self.assertFalse(self._nes_helper.suspend('test-accountid', 'test-customerid'))
        post.assert_called_with(
            'localhost/v2/customers/test-customerid/suspendByEntitlementId',
            headers={'Content-Type': 'application/json', 'x-app-key': 'zeus', 'Authorization': 'sso-jwt testJWT'},
            json={'entitlementId': 'test-accountid', 'suspendReason': 'POLICY'},
            timeout=30
        )
        setex.assert_called_with('nes-state', timedelta(minutes=10), 'DOWN')

    @patch('zeus.events.suspension.nes_helper.Redis.setex')
    @patch('zeus.events.suspension.nes_helper.requests.get', return_value=MagicMock(status_code=200, json=MagicMock(return_value={'status': 'ACTIVE'})))
    @patch('zeus.events.suspension.nes_helper.requests.post', return_value=MagicMock(status_code=204))
    def test_suspend_success(self, post, get, setex):
        self.assertTrue(self._nes_helper.suspend('test-accountid', 'test-customerid'))
        post.assert_called_with(
            'localhost/v2/customers/test-customerid/suspendByEntitlementId',
            headers={'Content-Type': 'application/json', 'x-app-key': 'zeus', 'Authorization': 'sso-jwt testJWT'},
            json={'entitlementId': 'test-accountid', 'suspendReason': 'POLICY'},
            timeout=30
        )
        self.assertFalse(setex.called)

    @patch('zeus.events.suspension.nes_helper.Redis.setex')
    @patch('zeus.events.suspension.nes_helper.requests.get', return_value=MagicMock(status_code=200, json=MagicMock(return_value={'status': 'ACTIVE'})))
    @patch('zeus.events.suspension.nes_helper.requests.post', return_value=MagicMock(status_code=404))
    def test_suspend_fail(self, post, get, setex):
        self.assertFalse(self._nes_helper.suspend('test-accountid', 'test-customerid'))
        post.assert_called_with(
            'localhost/v2/customers/test-customerid/suspendByEntitlementId',
            headers={'Content-Type': 'application/json', 'x-app-key': 'zeus', 'Authorization': 'sso-jwt testJWT'},
            json={'entitlementId': 'test-accountid', 'suspendReason': 'POLICY'},
            timeout=30
        )
        setex.assert_called_with('nes-state', timedelta(minutes=10), 'DOWN')

    @patch('zeus.events.suspension.nes_helper.Redis.setex')
    @patch('zeus.events.suspension.nes_helper.requests.get', return_value=MagicMock(status_code=200, json=MagicMock(return_value={'status': 'SUSPENDED'})))
    @patch('zeus.events.suspension.nes_helper.requests.post', return_value=MagicMock(status_code=204))
    def test_suspend_already_suspended(self, post, get, setex):
        # Verify suspension returns true AND that post was not called
        self.assertTrue(self._nes_helper.suspend('test-accountid', 'test-customerid'))
        self.assertFalse(post.called)
        self.assertFalse(setex.called)

    @patch('zeus.events.suspension.nes_helper.Redis.setex')
    @patch('zeus.events.suspension.nes_helper.requests.get', return_value=MagicMock(status_code=200, json=MagicMock(return_value={'status': 'SUSPENDED'})))
    @patch('zeus.events.suspension.nes_helper.requests.post', side_effect=Timeout())
    def test_reinstate_exception(self, post, get, setex):
        self.assertFalse(self._nes_helper.reinstate('test-accountid', 'test-customerid'))
        post.assert_called_with(
            'localhost/v2/customers/test-customerid/reinstateByEntitlementId',
            headers={'Content-Type': 'application/json', 'x-app-key': 'zeus', 'Authorization': 'sso-jwt testJWT'},
            json={'entitlementId': 'test-accountid', 'suspendReason': 'POLICY'},
            timeout=30
        )
        setex.assert_called_with('nes-state', timedelta(minutes=10), 'DOWN')

    @patch('zeus.events.suspension.nes_helper.Redis.setex')
    @patch('zeus.events.suspension.nes_helper.requests.get', return_value=MagicMock(status_code=200, json=MagicMock(return_value={'status': 'SUSPENDED'})))
    @patch('zeus.events.suspension.nes_helper.requests.post', return_value=MagicMock(status_code=204))
    def test_reinstate_success(self, post, get, setex):
        self.assertTrue(self._nes_helper.reinstate('test-accountid', 'test-customerid'))
        post.assert_called_with(
            'localhost/v2/customers/test-customerid/reinstateByEntitlementId',
            headers={'Content-Type': 'application/json', 'x-app-key': 'zeus', 'Authorization': 'sso-jwt testJWT'},
            json={'entitlementId': 'test-accountid', 'suspendReason': 'POLICY'},
            timeout=30
        )
        self.assertFalse(setex.called)

    @patch('zeus.events.suspension.nes_helper.Redis.setex')
    @patch('zeus.events.suspension.nes_helper.requests.get', return_value=MagicMock(status_code=200, json=MagicMock(return_value={'status': 'SUSPENDED'})))
    @patch('zeus.events.suspension.nes_helper.requests.post', return_value=MagicMock(status_code=404))
    def test_reinstate_fail(self, post, get, setex):
        self.assertFalse(self._nes_helper.reinstate('test-accountid', 'test-customerid'))
        post.assert_called_with(
            'localhost/v2/customers/test-customerid/reinstateByEntitlementId',
            headers={'Content-Type': 'application/json', 'x-app-key': 'zeus', 'Authorization': 'sso-jwt testJWT'},
            json={'entitlementId': 'test-accountid', 'suspendReason': 'POLICY'},
            timeout=30
        )
        setex.assert_called_with('nes-state', timedelta(minutes=10), 'DOWN')

    @patch('zeus.events.suspension.nes_helper.Redis.setex')
    @patch('zeus.events.suspension.nes_helper.requests.get', return_value=MagicMock(status_code=200, json=MagicMock(return_value={'status': 'ACTIVE'})))
    @patch('zeus.events.suspension.nes_helper.requests.post', return_value=MagicMock(status_code=204))
    def test_reinstate_already_active(self, post, get, setex):
        # Verify suspension returns true AND that post was not called
        self.assertTrue(self._nes_helper.reinstate('test-accountid', 'test-customerid'))
        self.assertFalse(post.called)
        self.assertFalse(setex.called)

    @patch('zeus.events.suspension.nes_helper.Redis.setex')
    @patch('zeus.events.suspension.nes_helper.requests.get', return_value=MagicMock(status_code=200, json=MagicMock(return_value={'status': 'SUSPENDED'})))
    def test_entitlement_status_success(self, get, setex):
        status = self._nes_helper._get_entitlement_status('test-accountid', 'test-customerid')
        self.assertEqual('SUSPENDED', status)
        get.assert_called_with(
            'localhost/v2/customers/test-customerid/entitlements/test-accountid',
            headers={'Content-Type': 'application/json', 'x-app-key': 'zeus', 'Authorization': 'sso-jwt testJWT'},
            timeout=30
        )
        self.assertFalse(setex.called)

    @patch('zeus.events.suspension.nes_helper.Redis.setex')
    @patch('zeus.events.suspension.nes_helper.requests.get', return_value=MagicMock(status_code=500))
    def test_entitlement_status_error(self, get, setex):
        status = self._nes_helper._get_entitlement_status('test-accountid', 'test-customerid')
        self.assertEqual('Failed to get entitlement status', status)
        get.assert_called_with(
            'localhost/v2/customers/test-customerid/entitlements/test-accountid',
            headers={'Content-Type': 'application/json', 'x-app-key': 'zeus', 'Authorization': 'sso-jwt testJWT'},
            timeout=30
        )
        setex.assert_called_with('nes-state', timedelta(minutes=10), 'DOWN')

    @patch('zeus.events.suspension.nes_helper.Redis.setex')
    @patch('zeus.events.suspension.nes_helper.requests.get', return_value=MagicMock(status_code=404))
    def test_entitlement_status_404_error(self, get, setex):
        status = self._nes_helper._get_entitlement_status('test-accountid', 'test-customerid')
        self.assertEqual('Failed to get entitlement status', status)
        get.assert_called_with(
            'localhost/v2/customers/test-customerid/entitlements/test-accountid',
            headers={'Content-Type': 'application/json', 'x-app-key': 'zeus', 'Authorization': 'sso-jwt testJWT'},
            timeout=30
        )
        self.assertFalse(setex.called)

    @patch('zeus.events.suspension.nes_helper.Redis.setex')
    @patch('zeus.events.suspension.nes_helper.requests.get', side_effect=Exception('exception thrown'))
    def test_entitlement_status_exception(self, get, setex):
        status = self._nes_helper._get_entitlement_status('test-accountid', 'test-customerid')
        self.assertEqual('Exception thrown while trying to get entitlement status', status)
        get.assert_called_with(
            'localhost/v2/customers/test-customerid/entitlements/test-accountid',
            headers={'Content-Type': 'application/json', 'x-app-key': 'zeus', 'Authorization': 'sso-jwt testJWT'},
            timeout=30
        )
        setex.assert_called_with('nes-state', timedelta(minutes=10), 'DOWN')

    @patch.dict(os.environ, {'DIABLO_USE_NES': 'False', 'ALL_USE_NES': 'False'})
    def test_get_use_nes_none(self):
        self.assertFalse(self._nes_helper.get_use_nes({'hosted_status': 'HOSTED', 'data': {'domainQuery': {'host': {'product': 'diablo'}}}}))

    @patch.dict(os.environ, {'DIABLO_USE_NES': 'False', 'ALL_USE_NES': 'False'})
    def test_get_use_nes_product_false(self):
        self.assertFalse(self._nes_helper.get_use_nes({'hosted_status': 'HOSTED', 'data': {'domainQuery': {'host': {'product': 'diablo'}}}}))

    @patch.dict(os.environ, {'DIABLO_USE_NES': 'True'})
    @patch.dict(os.environ, {'ALL_USE_NES': 'False'})
    def test_get_use_nes_product_true(self):
        print(os.environ)
        self.assertTrue(self._nes_helper.get_use_nes(self.HOSTED_DIABLO_DATA))

    @patch.dict(os.environ, {'DIABLO_USE_NES': 'False', 'ALL_USE_NES': 'True'})
    def test_get_use_nes_all_true(self):
        self.assertTrue(self._nes_helper.get_use_nes({'hosted_status': 'HOSTED', 'data': {'domainQuery': {'host': {'product': 'diablo'}}}}))

    def test_get_use_nes_not_hosted(self):
        self.assertFalse(self._nes_helper.get_use_nes({'hosted_status': 'REGISTERED'}))

    def test_get_use_nes_no_product(self):
        self.assertFalse(self._nes_helper.get_use_nes({'hosted_status': 'HOSTED'}))

    @patch('zeus.events.suspension.nes_helper.Redis.get', return_value='')
    def test_set_nes_state_not_set(self, get):
        # If the state isn't set, we assume it's good
        self.assertTrue(self._nes_helper.get_nes_state())

    @patch('zeus.events.suspension.nes_helper.Redis.get', return_value=b'DOWN')
    @patch('zeus.events.suspension.nes_helper.Redis.setex', return_value=None)
    def test_set_nes_state_down(self, redisget, redissetex):
        self._nes_helper.set_nes_state('DOWN')
        self.assertFalse(self._nes_helper.get_nes_state())

    @patch('zeus.events.suspension.nes_helper.requests.get', return_value=MagicMock(status_code=200, json=MagicMock(return_value=SUBSCRIPTION_DATA)))
    def test_get_subscriptions(self, get):
        result = self._nes_helper.get_subscriptions('769ffce0-819c-4364-8a73-ef884a2d64b9', 'websiteBuilder')
        self.assertEqual(result, self.SUBSCRIPTION_DATA)
        self.assertEqual(1, get.call_count)
        get.assert_called_with('localhost/v2/customers/769ffce0-819c-4364-8a73-ef884a2d64b9/subscriptions', headers={'Content-Type': 'application/json', 'x-app-key': 'zeus', 'Authorization': 'sso-jwt testJWT'}, timeout=30, params={'limit': 250, 'offset': 0, 'productFamilies': 'websiteBuilder'})

    @patch('zeus.events.suspension.nes_helper.requests.get', return_value=MagicMock(status_code=200, json=MagicMock(return_value=SUBSCRIPTION_DATA)))
    def test_get_subscriptions_251(self, get):
        get.return_value.json.side_effect = [[self.SUBSCRIPTION_DATA[0]] * 250, [self.SUBSCRIPTION_DATA[0]]]
        result = self._nes_helper.get_subscriptions('769ffce0-819c-4364-8a73-ef884a2d64b9', 'websiteBuilder')
        self.assertEqual(251, len(result))
        self.assertEqual(2, get.call_count)
        get.assert_any_call('localhost/v2/customers/769ffce0-819c-4364-8a73-ef884a2d64b9/subscriptions', headers={'Content-Type': 'application/json', 'x-app-key': 'zeus', 'Authorization': 'sso-jwt testJWT'}, timeout=30, params={'limit': 250, 'offset': 0, 'productFamilies': 'websiteBuilder'})
        get.assert_any_call('localhost/v2/customers/769ffce0-819c-4364-8a73-ef884a2d64b9/subscriptions', headers={'Content-Type': 'application/json', 'x-app-key': 'zeus', 'Authorization': 'sso-jwt testJWT'}, timeout=30, params={'limit': 250, 'offset': 250, 'productFamilies': 'websiteBuilder'})

    @patch('zeus.events.suspension.nes_helper.requests.get', return_value=MagicMock(status_code=200, json=MagicMock(return_value=SUBSCRIPTION_DATA)))
    def test_get_subscriptions_403(self, get):
        get.side_effect = [
            MagicMock(status_code=403, json=MagicMock(return_value={})),
            MagicMock(status_code=200, json=MagicMock(return_value=self.SUBSCRIPTION_DATA))
        ]
        result = self._nes_helper.get_subscriptions('769ffce0-819c-4364-8a73-ef884a2d64b9', 'websiteBuilder')
        self.assertEqual(result, self.SUBSCRIPTION_DATA)
        self.assertEqual(2, get.call_count)
        get.assert_called_with('localhost/v2/customers/769ffce0-819c-4364-8a73-ef884a2d64b9/subscriptions', headers={'Content-Type': 'application/json', 'x-app-key': 'zeus', 'Authorization': 'sso-jwt testJWT'}, timeout=30, params={'limit': 250, 'offset': 0, 'productFamilies': 'websiteBuilder'})

    @patch('zeus.events.suspension.nes_helper.NESHelper.get_subscriptions', return_value=SUBSCRIPTION_DATA)
    def test_get_entitlements_from_subscriptions(self, get_subs):
        result = self._nes_helper.get_entitlements_from_subscriptions('769ffce0-819c-4364-8a73-ef884a2d64b9', 'websiteBuilder', 'websitesAndMarketing')
        self.assertEqual(result, ['b1352611-ed1f-11ed-81b4-0050569a00bd', '4b609483-ed1f-11ed-81b4-0050569a00bd'])
        get_subs.assert_called_with('769ffce0-819c-4364-8a73-ef884a2d64b9', 'websiteBuilder')

    @patch('zeus.events.suspension.nes_helper.NESHelper.get_subscriptions', return_value=SUBSCRIPTION_DATA)
    def test_get_entitlements_from_subscriptions_no_matching_products(self, get_subs):
        result = self._nes_helper.get_entitlements_from_subscriptions('769ffce0-819c-4364-8a73-ef884a2d64b9', 'websiteBuilder', 'random')
        self.assertEqual(result, [])
        get_subs.assert_called_with('769ffce0-819c-4364-8a73-ef884a2d64b9', 'websiteBuilder')
