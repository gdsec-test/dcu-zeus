from datetime import timedelta
from unittest import TestCase

from mock import MagicMock, patch

from settings import UnitTestConfig
from zeus.utils.shopperapi import ShopperAPI


class TestShopperApi(TestCase):
    def setUp(self):
        self._shopperapi = ShopperAPI(UnitTestConfig)

    @patch.object(ShopperAPI, 'get_shopper_id_from_customer_id', return_value='7890')
    def test_get_shopper_id_from_dict_customer_id(self, get_shopper_id_from_customer_id):
        actual = self._shopperapi.get_shopper_id_from_dict({'data': {'domainQuery': {'shopperInfo': {'customerId': '1234-5678'}}}})
        self.assertEqual(actual, '7890')

    def test_get_shopper_id_from_dict_no_customer_id(self):
        actual = self._shopperapi.get_shopper_id_from_dict({'data': {'domainQuery': {'shopperInfo': {'shopperId': '1234'}}}})
        self.assertEqual(actual, '1234')

    def test_get_shopper_id_from_dict_none(self):
        actual = self._shopperapi.get_shopper_id_from_dict({})
        self.assertIsNone(actual)

    def test_get_shopper_id_from_dict_child(self):
        data = {'data': {'domainQuery': {'apiReseller': {'parent': '1234', 'child': '5678'}}}}
        actual = self._shopperapi.get_shopper_id_from_dict(data)
        self.assertEqual(actual, '5678')

    @patch.object(ShopperAPI, 'get_shopper_id_from_customer_id', return_value='7890')
    def test_get_shopper_id_from_dict_child_customer_id(self, get_shopper_id_from_customer_id):
        data = {'data': {'domainQuery': {'apiReseller': {'parentCustomerId': 'abc', 'childCustomerId': 'def'}}}}
        actual = self._shopperapi.get_shopper_id_from_dict(data)
        self.assertEqual(actual, '7890')
        get_shopper_id_from_customer_id.assert_called_with('def')

    @patch.object(ShopperAPI, 'get_shopper_id_from_customer_id', return_value='7890')
    def test_get_host_shopper_id_from_dict_customer_id(self, get_shopper_id_from_customer_id):
        actual = self._shopperapi.get_host_shopper_id_from_dict({'data': {'domainQuery': {'host': {'customerId': '1234-5678'}}}})
        self.assertEqual(actual, '7890')

    def test_get_host_shopper_id_from_dict_no_customer_id(self):
        actual = self._shopperapi.get_host_shopper_id_from_dict({'data': {'domainQuery': {'host': {'shopperId': '1234'}}}})
        self.assertEqual(actual, '1234')

    def test_get_host_shopper_id_from_dict_none(self):
        actual = self._shopperapi.get_host_shopper_id_from_dict({})
        self.assertIsNone(actual)

    @patch.object(ShopperAPI, 'get_shopper_id_from_customer_id', return_value='7890')
    def test_get_list_of_shopper_ids_to_notify(self, get_shopper_id_from_customer_id):
        data = {'data': {'domainQuery': {'apiReseller': {'parent': '1234', 'child': '4567'}}}}
        actual = self._shopperapi.get_list_of_ids_to_notify(data)
        self.assertEqual(actual, ['1234', '4567'])
        self.assertFalse(get_shopper_id_from_customer_id.called)

    @patch.object(ShopperAPI, 'get_shopper_id_from_customer_id', return_value='1234')
    def test_get_list_of_ids_to_notify_convert_customer_to_shopper(self, get_shopper_id_from_customer_id):
        data = {'data': {'domainQuery': {'apiReseller': {'parentCustomerId': 'abc', 'childCustomerId': 'def'}}}}
        actual = self._shopperapi.get_list_of_ids_to_notify(data)
        self.assertEqual(actual, ['1234', '1234'])
        get_shopper_id_from_customer_id.assert_called_with('def')

    @patch.object(ShopperAPI, 'get_shopper_id_from_customer_id', return_value='7890')
    def test_get_list_of_ids_to_notify_no_api_reseller(self, get_shopper_id_from_customer_id):
        data = {'data': {'domainQuery': {'shopperInfo': {'customerId': '1234-5678'}}}}
        actual = self._shopperapi.get_list_of_ids_to_notify(data)
        self.assertEqual(actual, ['7890'])
        get_shopper_id_from_customer_id.assert_called_with('1234-5678')

    @patch('zeus.utils.shopperapi.Redis.get', return_value=b'customerIdRedis')
    def test_get_customer_id_from_shopper_redis(self, get):
        customerid = self._shopperapi.get_customer_id_from_shopper_id('123456')
        get.assert_called_with('shopper-id-key-123456')
        self.assertEqual(customerid, 'customerIdRedis')

    @patch('zeus.utils.shopperapi.Redis.get', return_value='')
    @patch('zeus.utils.shopperapi.Redis.setex')
    @patch('zeus.utils.shopperapi.requests.get', return_value=MagicMock(status_code=200, json=MagicMock(return_value={'customerId': 'customerIdApi'})))
    def test_get_customer_id_from_shopper_api(self, requests_get, setex, redis_get):
        customerid = self._shopperapi.get_customer_id_from_shopper_id('123456')
        self.assertEqual(customerid, 'customerIdApi')
        redis_get.assert_called_with('shopper-id-key-123456')
        requests_get.assert_called_with(
            'test_shopper_api/v1/shoppers/123456',
            params={'includes': 'contact,preference', 'auditClientIp': 'zeus'},
            cert=('zeus_test_cert', 'zeus_test_key'))
        setex.assert_called_with('shopper-id-key-123456', 'customerIdApi', timedelta(days=5))
