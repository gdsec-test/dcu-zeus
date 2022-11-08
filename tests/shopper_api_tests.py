from mock import patch
from mockredis import mock_redis_client
from nose.tools import assert_equal, assert_is_none

from settings import UnitTestConfig
from zeus.utils.shopperapi import ShopperAPI


class TestShopperApi:
    @classmethod
    def setup(cls):
        cls._shopperapi = ShopperAPI(UnitTestConfig)
        cls._shopperapi.redis = mock_redis_client(host='0.0.0.0', port=6379, db=0)

    @patch.object(ShopperAPI, 'get_shopper_id_from_customer_id', return_value='7890')
    def test_get_shopper_id_from_dict_customer_id(self, get_shopper_id_from_customer_id):
        actual = self._shopperapi.get_shopper_id_from_dict({'data': {'domainQuery': {'shopperInfo': {'customerId': '1234-5678'}}}})
        assert_equal(actual, '7890')

    def test_get_shopper_id_from_dict_no_customer_id(self):
        actual = self._shopperapi.get_shopper_id_from_dict({'data': {'domainQuery': {'shopperInfo': {'shopperId': '1234'}}}})
        assert_equal(actual, '1234')

    def test_get_shopper_id_from_dict_none(self):
        actual = self._shopperapi.get_shopper_id_from_dict({})
        assert_is_none(actual)

    def test_get_shopper_id_from_dict_child(self):
        data = {'data': {'domainQuery': {'apiReseller': {'parent': '1234', 'child': '5678'}}}}
        actual = self._shopperapi.get_shopper_id_from_dict(data)
        assert_equal(actual, '5678')

    @patch.object(ShopperAPI, 'get_shopper_id_from_customer_id', return_value='7890')
    def test_get_shopper_id_from_dict_child_customer_id(self, get_shopper_id_from_customer_id):
        data = {'data': {'domainQuery': {'apiReseller': {'parentCustomerId': 'abc', 'childCustomerId': 'def'}}}}
        actual = self._shopperapi.get_shopper_id_from_dict(data)
        assert_equal(actual, '7890')
        assert get_shopper_id_from_customer_id.called

    @patch.object(ShopperAPI, 'get_shopper_id_from_customer_id', return_value='7890')
    def test_get_host_shopper_id_from_dict_customer_id(self, get_shopper_id_from_customer_id):
        actual = self._shopperapi.get_host_shopper_id_from_dict({'data': {'domainQuery': {'host': {'customerId': '1234-5678'}}}})
        assert_equal(actual, '7890')

    def test_get_host_shopper_id_from_dict_no_customer_id(self):
        actual = self._shopperapi.get_host_shopper_id_from_dict({'data': {'domainQuery': {'host': {'shopperId': '1234'}}}})
        assert_equal(actual, '1234')

    def test_get_host_shopper_id_from_dict_none(self):
        actual = self._shopperapi.get_host_shopper_id_from_dict({})
        assert_is_none(actual)

    @patch.object(ShopperAPI, 'get_shopper_id_from_customer_id', return_value='7890')
    def test_get_list_of_shopper_ids_to_notify(self, get_shopper_id_from_customer_id):
        data = {'data': {'domainQuery': {'apiReseller': {'parent': '1234', 'child': '4567'}}}}
        actual = self._shopperapi.get_list_of_ids_to_notify(data)
        assert_equal(actual, ['1234', '4567'])

    @patch.object(ShopperAPI, 'get_shopper_id_from_customer_id', return_value='1234')
    def test_get_list_of_ids_to_notify_convert_customer_to_shopper(self, get_shopper_id_from_customer_id):
        data = {'data': {'domainQuery': {'apiReseller': {'parentCustomerId': 'abc', 'childCustomerId': 'def'}}}}
        actual = self._shopperapi.get_list_of_ids_to_notify(data)
        assert_equal(actual, ['1234', '1234'])
        assert get_shopper_id_from_customer_id.called

    @patch.object(ShopperAPI, 'get_shopper_id_from_customer_id', return_value='7890')
    def test_get_list_of_ids_to_notify_no_api_reseller(self, get_shopper_id_from_customer_id):
        data = {'data': {'domainQuery': {'shopperInfo': {'customerId': '1234-5678'}}}}
        actual = self._shopperapi.get_list_of_ids_to_notify(data)
        assert_equal(actual, ['7890'])
