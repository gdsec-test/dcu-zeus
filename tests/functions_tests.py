from nose.tools import assert_equal, assert_is_none

from zeus.utils.functions import (get_domain_create_date_from_dict,
                                  get_host_abuse_email_from_dict,
                                  get_host_brand_from_dict,
                                  get_list_of_ids_to_notify,
                                  get_parent_child_shopper_ids_from_dict,
                                  get_shopper_create_date_from_dict,
                                  get_shopper_id_from_dict)


class TestFunctions:
    def test_get_shopper_id_from_dict_none(self):
        actual = get_shopper_id_from_dict(None)
        assert_is_none(actual)

    def test_get_shopper_id_from_dict(self):
        data = {'data': {'domainQuery': {'shopperInfo': {'shopperId': '1234'}}}}
        actual = get_shopper_id_from_dict(data)
        assert_equal(actual, '1234')

    def test_get_parent_child_shopper_ids_from_dict_none(self):
        actual = get_parent_child_shopper_ids_from_dict(None)
        assert_is_none(actual)

    def test_get_parent_child_shopper_ids_from_dict_no_parent(self):
        data = {'data': {'domainQuery': {'apiReseller': {'parent': None, 'child': '5678'}}}}
        actual = get_parent_child_shopper_ids_from_dict(data)
        assert_is_none(actual)

    def test_get_parent_child_shopper_ids_from_dict(self):
        data = {'data': {'domainQuery': {'apiReseller': {'parent': '1234', 'child': '5678'}}}}
        actual = get_parent_child_shopper_ids_from_dict(data)
        assert_equal(actual, ['1234', '5678'])

    def test_get_domain_create_date_from_dict_none(self):
        actual = get_domain_create_date_from_dict(None)
        assert_is_none(actual)

    def test_get_domain_create_date_from_dict(self):
        data = {'data': {'domainQuery': {'registrar': {'domainCreateDate': 'Jan 1, 1970'}}}}
        actual = get_domain_create_date_from_dict(data)
        assert_equal(actual, 'Jan 1, 1970')

    def test_get_shopper_create_date_from_dict_none(self):
        actual = get_shopper_create_date_from_dict(None)
        assert_is_none(actual)

    def test_get_shopper_create_date_from_dict(self):
        data = {'data': {'domainQuery': {'shopperInfo': {'shopperCreateDate': 'Jan 1, 1970'}}}}
        actual = get_shopper_create_date_from_dict(data)
        assert_equal(actual, 'Jan 1, 1970')

    def test_get_host_abuse_email_from_dict_none(self):
        actual = get_host_abuse_email_from_dict(None)
        assert_equal(actual, [])

    def test_get_host_abuse_email_from_dict_none2(self):
        data = {'data': {'domainQuery': {'host': {'hostingAbuseEmail': None}}}}
        actual = get_host_abuse_email_from_dict(data)
        assert_equal(actual, [])

    def test_get_host_abuse_email_from_dict_single(self):
        data = {'data': {'domainQuery': {'host': {'hostingAbuseEmail': 'xxx@xxx.com'}}}}
        actual = get_host_abuse_email_from_dict(data)
        assert_equal(actual, ['xxx@xxx.com'])

    def test_get_host_abuse_email_from_dict_list_abuse(self):
        data = {'data': {'domainQuery': {'host': {'hostingAbuseEmail': ['abuse@xxx.com']}}}}
        actual = get_host_abuse_email_from_dict(data)
        assert_equal(actual, ['abuse@xxx.com'])

    def test_get_host_abuse_email_from_dict_list_non_abuse(self):
        data = {'data': {'domainQuery': {'host': {'hostingAbuseEmail': ['xxx@xxx.com']}}}}
        actual = get_host_abuse_email_from_dict(data)
        assert_equal(actual, ['xxx@xxx.com'])

    def test_get_host_brand_from_dict_none(self):
        actual = get_host_brand_from_dict(None)
        assert_is_none(actual)

    def test_get_host_brand_from_dict(self):
        data = {'data': {'domainQuery': {'host': {'brand': 'GODADDY'}}}}
        actual = get_host_brand_from_dict(data)
        assert_equal(actual, 'GODADDY')

    def test_get_list_of_ids_to_notify_none(self):
        actual = get_list_of_ids_to_notify({})
        assert_equal(actual, [])

    def test_get_list_of_ids_to_notify(self):
        data = {'data': {'domainQuery': {'apiReseller': {'parent': '1234', 'child': '4567'}}}}
        actual = get_list_of_ids_to_notify(data)
        assert_equal(actual, ['1234', '4567'])

    def test_get_shopper_create_date_none(self):
        actual = get_shopper_create_date_from_dict(None)
        assert_is_none(actual)

    def test_get_shopper_create_date(self):
        data = {'data': {'domainQuery': {'shopperInfo': {'shopperCreateDate': '1 Jan, 1970'}}}}
        actual = get_shopper_create_date_from_dict(data)
        assert_equal(actual, '1 Jan, 1970')
