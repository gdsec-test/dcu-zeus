import os

from mock import MagicMock, patch
from nose.tools import assert_equal, assert_false, assert_true
from requests.exceptions import Timeout

from settings import UnitTestConfig
from zeus.events.suspension.nes_helper import NESHelper


class TestNESHelper:
    HOSTED_DIABLO_DATA = {'hosted_status': 'HOSTED', 'data': {'domainQuery': {'host': {'product': 'diablo'}}}}
    MOCK_ENTITLEMENT_SUSPENDED_RESPONSE = MagicMock()
    MOCK_ENTITLEMENT_SUSPENDED_RESPONSE.status_code = 200
    MOCK_ENTITLEMENT_SUSPENDED_RESPONSE.json.return_value = {
        'status': 'SUSPENDED',
    }

    @classmethod
    def setup(cls):
        cls._nes_helper = NESHelper(UnitTestConfig)

    @patch('requests.post', side_effect=Timeout())
    def test_suspend_exception(self, post):
        assert_false(self._nes_helper.suspend('test-accountid', 'test-customerid'))

    @patch('requests.post', return_value=MagicMock(status_code=204))
    def test_suspend_success(self, post):
        assert_true(self._nes_helper.suspend('test-accountid', 'test-customerid'))

    @patch('requests.post', return_value=MagicMock(status_code=404))
    def test_suspend_fail(self, post):
        assert_false(self._nes_helper.suspend('test-accountid', 'test-customerid'))

    @patch('requests.post', return_value=MagicMock(status_code=204))
    @patch('requests.get')
    @patch('zeus.events.suspension.nes_helper.NESHelper._get_jwt', return_value='testJWT')
    def test_suspend_already_suspended(self, post, get, get_jwt):
        get.return_value = self.MOCK_ENTITLEMENT_SUSPENDED_RESPONSE
        # Verify suspension returns true AND that post was not called
        assert_true(self._nes_helper.suspend('test-accountid', 'test-customerid'))
        assert_false(post.called)

    @patch('requests.post', side_effect=Timeout())
    def test_reinstate_exception(self, post):
        assert_false(self._nes_helper.reinstate('test-accountid', 'test-customerid'))

    @patch('requests.post', return_value=MagicMock(status_code=204))
    def test_reinstate_success(self, post):
        assert_true(self._nes_helper.reinstate('test-accountid', 'test-customerid'))

    @patch('requests.post', return_value=MagicMock(status_code=404))
    def test_reinstate_fail(self, post):
        assert_false(self._nes_helper.reinstate('test-accountid', 'test-customerid'))

    @patch('requests.post', return_value=MagicMock(status_code=204))
    @patch('requests.get')
    @patch('zeus.events.suspension.nes_helper.NESHelper._get_jwt', return_value='testJWT')
    def test_reinstate_already_active(self, post, get, get_jwt):
        mock_entitlement_active_response = MagicMock()
        mock_entitlement_active_response.status_code = 200
        mock_entitlement_active_response.json.return_value = {
            'status': 'ACTIVE'
        }
        get.return_value = mock_entitlement_active_response

        # Verify suspension returns true AND that post was not called
        assert_true(self._nes_helper.reinstate('test-accountid', 'test-customerid'))
        assert_false(post.called)

    @patch('requests.get')
    @patch('zeus.events.suspension.nes_helper.NESHelper._get_jwt', return_value='testJWT')
    def test_entitlement_status_success(self, get, _get_jwt):
        mock_entitlement_suspended_response = MagicMock()
        mock_entitlement_suspended_response.status_code = 200
        mock_entitlement_suspended_response.json.return_value = {
            'status': 'ACTIVE'
        }
        get.return_value = mock_entitlement_suspended_response
        assert_equal(self._nes_helper._check_entitlement_status('test-accountid', 'test-customerid'), 'SUSPENDED')

    # @patch('requests.get', return_value=MagicMock(status_code=404))
    # @patch('zeus.events.suspension.nes_helper.NESHelper._get_jwt', return_value='testJWT')
    # def test_entitlement_status_error(self, get, get_jwt):
    #     assert_equal('Failed to get entitlement status', self._nes_helper._check_entitlement_status('test-accountid', 'test-customerid'))

    # @patch('requests.get', sideEffect=Timeout())
    # @patch('zeus.events.suspension.nes_helper.NESHelper._get_jwt', return_value='testJWT')
    # def test_entitlement_status_exception(self, get, get_jwt):
    #     assert_equal('Exception thrown while trying to get entitlement status', self._nes_helper._check_entitlement_status('test-accountid', 'test-customerid'))

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
