from nose.tools import assert_equal, assert_is_none

from settings import TestingConfig
from zeus.utils.functions import get_list_of_ids_to_notify, \
    get_domain_create_date_from_dict, \
    get_shopper_create_date_from_dict


class TestNotificationHelper:

    @classmethod
    def setup(cls):
        cls._shopper = '1234'
        cls._domain = 'google.com'
        cls._config = TestingConfig()

    def test_get_list_of_ids_to_notify_none(self):
        actual = get_list_of_ids_to_notify({})
        assert_equal(actual, [])

    def test_get_list_of_ids_to_notify(self):
        data = {'data': {'domainQuery': {'apiReseller': {'parent': '1234', 'child': '4567'}}}}
        actual = get_list_of_ids_to_notify(data)
        assert_equal(actual, ['1234', '4567'])

    def test_get_domain_create_date_from_dict_none(self):
        actual = get_domain_create_date_from_dict(None)
        assert_is_none(actual)

    def test_get_domain_create_date_from_dict(self):
        data = {'data': {'domainQuery': {'registrar': {'domainCreateDate': '1 Jan, 1970'}}}}
        actual = get_domain_create_date_from_dict(data)
        assert_equal(actual, '1 Jan, 1970')

    def test_get_shopper_create_date_none(self):
        actual = get_shopper_create_date_from_dict(None)
        assert_is_none(actual)

    def test_get_shopper_create_date(self):
        data = {'data': {'domainQuery': {'shopperInfo': {'shopperCreateDate': '1 Jan, 1970'}}}}
        actual = get_shopper_create_date_from_dict(data)
        assert_equal(actual, '1 Jan, 1970')
