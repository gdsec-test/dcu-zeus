from unittest import TestCase

from mock import MagicMock, patch

from settings import UnitTestConfig
from zeus.events.suspension.hosting_service import HostingService
from zeus.events.suspension.vps4 import VPS4


class TestHostingService(TestCase):
    DATA_NO_CUSTOMER_ID = {'data': {'domainQuery': {'host': {'shopperId': '1234567', 'entitlementId': 'test-entitlementID'}}}}
    DATA_WITH_CUSTOMER_ID = {'data': {'domainQuery': {'host': {'customerId': '1234-5678-9012', 'entitlementId': 'test-entitlementID'}}}}

    def setUp(self):
        self._hosting_service = HostingService(UnitTestConfig())
        self._vps4 = VPS4._get_jwt = MagicMock(return_value='fake-jwt')

    def test_suspend(self):
        actual = self._hosting_service.suspend('test-product', None, None)
        self.assertEqual(actual, 'Unsupported Product: test-product')

    def test_reinstate(self):
        actual = self._hosting_service.reinstate('test-product', None, None)
        self.assertEqual(actual, 'Unsupported Product: test-product')

    def test_cancel(self):
        actual = self._hosting_service.cancel('test-product', None)
        self.assertEqual(actual, 'Unsupported Product: test-product')

        actual = self._hosting_service.cancel('diablo', None)
        self.assertEqual(actual, 'Unsupported Operation: cancel')

    def test_block_content(self):
        actual = self._hosting_service.block_content('test-product', None)
        self.assertEqual(actual, 'Unsupported Product: test-product')

        actual = self._hosting_service.block_content('diablo', None)
        self.assertEqual(actual, 'Unsupported Operation: block_content')

    def test_unblock_content(self):
        actual = self._hosting_service.unblock_content('test-product', None)
        self.assertEqual(actual, 'Unsupported Product: test-product')

        actual = self._hosting_service.unblock_content('diablo', None)
        self.assertEqual(actual, 'Unsupported Operation: unblock_content')

    def test_delete_content(self):
        actual = self._hosting_service.delete_content('test-product', None)
        self.assertEqual(actual, 'Unsupported Product: test-product')

        actual = self._hosting_service.delete_content('diablo', None)
        self.assertEqual(actual, 'Unsupported Operation: delete_content')

    def test_delete_content_gocentral(self):
        actual = self._hosting_service.delete_content('gocentral', None)
        self.assertEqual(actual, 'Unsupported Operation: delete_content')

    # TODO CMAPT-5272: remove this test
    @patch('zeus.events.suspension.nes_helper.NESHelper.get_use_nes', return_value=False)
    @patch('zeus.events.suspension.diablo.Diablo.suspend', return_value=True)
    def test_use_nes_product_false(self, suspend, get_use_nes):
        self._hosting_service.suspend('diablo', 'test-guid', self.DATA_WITH_CUSTOMER_ID)
        suspend.assert_called_with(guid='test-guid', data=self.DATA_WITH_CUSTOMER_ID)

    # TODO CMAPT-5272: next TWO tests - remove the 'get_use_nes' mock value
    @patch('zeus.utils.shopperapi.ShopperAPI.get_customer_id_from_shopper_id', return_value='customerId')
    @patch('zeus.events.suspension.nes_helper.NESHelper.get_use_nes', return_value=True)
    @patch('zeus.events.suspension.nes_helper.NESHelper.suspend', return_value=True)
    def test_use_nes_product_true_no_customer(self, suspend, get_use_nes, get_customer_id_from_shopper):
        self._hosting_service.suspend('diablo', 'test-guid', self.DATA_NO_CUSTOMER_ID)
        get_customer_id_from_shopper.assert_called_with('1234567')
        suspend.assert_called_with('test-entitlementID', 'customerId')

    @patch('zeus.events.suspension.nes_helper.NESHelper.get_use_nes', return_value=True)
    @patch('zeus.events.suspension.nes_helper.NESHelper.suspend', return_value=True)
    def test_use_nes_product_true_customer_exists(self, suspend, get_use_nes):
        self._hosting_service.suspend('diablo', 'test-guid', self.DATA_WITH_CUSTOMER_ID)
        suspend.assert_called_with('test-entitlementID', '1234-5678-9012')
