from mock import patch
from nose.tools import assert_equal, assert_true

from settings import UnitTestConfig
from zeus.events.suspension.hosting_service import HostingService
from zeus.events.suspension.vps4 import VPS4


class TestHostingService:
    @classmethod
    @patch.object(VPS4, '_get_jwt', return_value='fake-jwt')
    def setup(cls, mock_vps):
        cls._hosting_service = HostingService(UnitTestConfig)

    def test_suspend(self):
        actual = self._hosting_service.suspend('test-product', None, None)
        assert_equal(actual, 'Unsupported Product: test-product')

    def test_reinstate(self):
        actual = self._hosting_service.reinstate('test-product', None, None)
        assert_equal(actual, 'Unsupported Product: test-product')

    def test_cancel(self):
        actual = self._hosting_service.cancel('test-product', None)
        assert_equal(actual, 'Unsupported Product: test-product')

        actual = self._hosting_service.cancel('diablo', None)
        assert_equal(actual, 'Unsupported Operation: cancel')

    def test_block_content(self):
        actual = self._hosting_service.block_content('test-product', None)
        assert_equal(actual, 'Unsupported Product: test-product')

        actual = self._hosting_service.block_content('diablo', None)
        assert_equal(actual, 'Unsupported Operation: block_content')

    def test_unblock_content(self):
        actual = self._hosting_service.unblock_content('test-product', None)
        assert_equal(actual, 'Unsupported Product: test-product')

        actual = self._hosting_service.unblock_content('diablo', None)
        assert_equal(actual, 'Unsupported Operation: unblock_content')

    def test_delete_content(self):
        actual = self._hosting_service.delete_content('test-product', None)
        assert_equal(actual, 'Unsupported Product: test-product')

        actual = self._hosting_service.delete_content('diablo', None)
        assert_equal(actual, 'Unsupported Operation: delete_content')

    # TODO CMAPT-5272: remove these tests
    @patch('zeus.events.suspension.nes_helper.NESHelper.get_use_nes', return_value=True)
    @patch('zeus.events.suspension.nes_helper.NESHelper.suspend', return_value=True)
    def test_use_nes_product_true(self, get_use_nes, suspend):
        self._hosting_service.suspend("diablo", "test-entitlementID", "test_data")
        assert_true(suspend.called)

    @patch('zeus.events.suspension.nes_helper.NESHelper.get_use_nes', return_value=True)
    @patch('zeus.events.suspension.diablo.Diablo.suspend', return_value=True)
    def test_use_nes_product_false(self, get_use_nes, suspend):
        self._hosting_service.suspend("diablo", "test-entitlementID", "test_data")
        assert_true(suspend.called)
