import os

from mock import MagicMock, patch
from nose.tools import assert_false, assert_true
from requests.exceptions import Timeout

from settings import UnitTestConfig
from zeus.events.suspension.nes_helper import NESHelper


class TestNESHelper:
    HOSTED_DIABLO_DATA = {'hosted_status': 'HOSTED', 'data': {'domainQuery': {'host': {'product': 'diablo'}}}}

    @classmethod
    def setup(cls):
        cls._nes_helper = NESHelper(UnitTestConfig)

    @patch('requests.post', side_effect=Timeout())
    @patch('zeus.events.suspension.nes_helper.NESHelper.wait_for_entitlement_status', return_value=True)
    def test_suspend_exception(self, post, wait_for_entitlement_status):
        assert_false(self._nes_helper.suspend('test-accountid', 'test-customerid'))

    @patch('requests.post', return_value=MagicMock(status_code=204))
    @patch('zeus.events.suspension.nes_helper.NESHelper.wait_for_entitlement_status', return_value=True)
    def test_suspend_success(self, post, wait_for_entitlement_status):
        assert_true(self._nes_helper.suspend('test-accountid', 'test-customerid'))

    @patch('requests.post', return_value=MagicMock(status_code=404))
    @patch('zeus.events.suspension.nes_helper.NESHelper.wait_for_entitlement_status', return_value=True)
    def test_suspend_fail(self, post, wait_for_entitlement_status):
        assert_false(self._nes_helper.suspend('test-accountid', 'test-customerid'))

    @patch('zeus.events.suspension.nes_helper.NESHelper._get_jwt', return_value='testJWT')
    @patch('zeus.events.suspension.nes_helper.NESHelper._check_entitlement_status', return_value='SUSPENDED')
    @patch('requests.post', return_value=MagicMock(status_code=204))
    def test_suspend_already_suspended(self, _get_jwt, _check_entitlement_status, post):
        # Verify suspension returns true AND that post was not called
        assert_true(self._nes_helper.suspend('test-accountid', 'test-customerid'))
        assert_false(post.called)

    @patch('requests.post', return_value=MagicMock(status_code=204))
    @patch('zeus.events.suspension.nes_helper.NESHelper.wait_for_entitlement_status', return_value=False)
    def test_suspend_entitlement_error(self, post, wait_for_entitlement_status):
        assert_false(self._nes_helper.suspend('test-accountid', 'test-entitlementid'))

    @patch('requests.post', side_effect=Timeout())
    @patch('zeus.events.suspension.nes_helper.NESHelper.wait_for_entitlement_status', return_value=True)
    def test_reinstate_exception(self, post, wait_for_entitlement_status):
        assert_false(self._nes_helper.reinstate('test-accountid', 'test-customerid'))

    @patch('requests.post', return_value=MagicMock(status_code=204))
    @patch('zeus.events.suspension.nes_helper.NESHelper.wait_for_entitlement_status', return_value=True)
    def test_reinstate_success(self, post, wait_for_entitlement_status):
        assert_true(self._nes_helper.reinstate('test-accountid', 'test-customerid'))

    @patch('requests.post', return_value=MagicMock(status_code=404))
    @patch('zeus.events.suspension.nes_helper.NESHelper.wait_for_entitlement_status', return_value=True)
    def test_reinstate_fail(self, post, wait_for_entitlement_status):
        assert_false(self._nes_helper.reinstate('test-accountid', 'test-customerid'))

    @patch('zeus.events.suspension.nes_helper.NESHelper._get_jwt', return_value='testJWT')
    @patch('zeus.events.suspension.nes_helper.NESHelper._check_entitlement_status', return_value='ACTIVE')
    @patch('requests.post', return_value=MagicMock(status_code=204))
    def test_reinstate_already_active(self, _get_jwt, _check_entitlement_status, post):
        # Verify suspension returns true AND that post was not called
        assert_true(self._nes_helper.reinstate('test-accountid', 'test-customerid'))
        assert_false(post.called)

    @patch('requests.post', return_value=MagicMock(status_code=204))
    @patch('zeus.events.suspension.nes_helper.NESHelper.wait_for_entitlement_status', return_value=False)
    def test_reinstate_entitlement_error(self, post, wait_for_entitlement_status):
        assert_false(self._nes_helper.suspend('test-accountid', 'test-entitlementid'))

    @patch('requests.get')
    # @patch('zeus.events.suspension.nes_helper.NESHelper._check_entitlement_status', return_value='SUSPENDED')
    def test_entitlement_status_sucess(self, get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 'SUSPENDED',
        }
        get.return_value = mock_response
        assert_true(self._nes_helper.wait_for_entitlement_status('test-accountid', 'test-customerid', 'SUSPENDED'))

    @patch('requests.get', return_value=MagicMock(status_code=404))
    def test_entitlement_status_fail(self, get):
        assert_false(self._nes_helper.wait_for_entitlement_status('test-accountid', 'test-customerid', 'SUSPENDED'))

    @patch('requests.get', side_effect=Timeout())
    def test_entitlement_status_exception(self, get):
        assert_false(self._nes_helper.wait_for_entitlement_status('test-accountid', 'test-customerid', 'SUSPENDED'))

    # TODO LKM: figure out what to do for this test - right now, as written, it's going to take TEN MINUTES to run, which we probably don't want...
    # @patch('requests.get', return_value=MagicMock(status_code=200, text=json.dumps({"status": "ACTIVE"})))
    # def test_entitlement_status_mismatch(self, get):
    #     assert_false(self._nes_helper.wait_for_entitlement_status('test-accountid', 'test-customerid', 'SUSPENDED'))

    @patch.dict(os.environ, {"DIABLO_USE_NES": "False", "ALL_USE_NES": "False"})
    def test_get_use_nes_none(self):
        assert_false(self._nes_helper.get_use_nes({'hosted_status': 'HOSTED', 'data': {'domainQuery': {'host': {'product': 'diablo'}}}}))

    @patch.dict(os.environ, {"DIABLO_USE_NES": "False", "ALL_USE_NES": "False", "VERTIGO_USE_NES": "True"})
    def test_get_use_nes_product_false(self):
        assert_false(self._nes_helper.get_use_nes({'hosted_status': 'HOSTED', 'data': {'domainQuery': {'host': {'product': 'diablo'}}}}))

    @patch.dict(os.environ, {'DIABLO_USE_NES': 'True'})
    @patch.dict(os.environ, {'ALL_USE_NES': 'False'})
    def test_get_use_nes_product_true(self):
        print(os.environ)
        assert_true(self._nes_helper.get_use_nes(self.HOSTED_DIABLO_DATA))

    @patch.dict(os.environ, {"DIABLO_USE_NES": "False", "ALL_USE_NES": "True"})
    def test_get_use_nes_all_true(self):
        assert_true(self._nes_helper.get_use_nes({'hosted_status': 'HOSTED', 'data': {'domainQuery': {'host': {'product': 'diablo'}}}}))

    def test_get_use_nes_not_hosted(self):
        assert_false(self._nes_helper.get_use_nes({'hosted_status': 'REGISTERED'}))

    def test_get_use_nes_no_product(self):
        assert_false(self._nes_helper.get_use_nes({'hosted_status': 'HOSTED'}))

    def test_set_nes_state(self):
        self._nes_helper.set_nes_state('UP')
        assert_true(self._nes_helper.get_nes_state())
