from nose.tools import assert_equal, assert_is_none

from zeus.utils.functions import (get_domain_create_date_from_dict,
                                  get_host_abuse_email_from_dict,
                                  get_host_brand_from_dict,
                                  get_kelvin_domain_id_from_dict,
                                  get_list_of_ids_to_notify,
                                  get_parent_child_shopper_ids_from_dict,
                                  get_shopper_create_date_from_dict,
                                  get_shopper_id_from_dict,
                                  get_ssl_subscriptions_from_dict,
                                  get_sucuri_product_from_dict, sanitize_url)


class TestFunctions:
    sucuri_malware_remover_product = 'Website Security Deluxe'

    def test_get_shopper_id_from_dict_none(self):
        actual = get_shopper_id_from_dict(None)
        assert_is_none(actual)

    def test_get_shopper_id_from_dict(self):
        data = {'data': {'domainQuery': {'shopperInfo': {'shopperId': '1234'}}}}
        actual = get_shopper_id_from_dict(data)
        assert_equal(actual, '1234')

    def test_get_shopper_id_from_dict_child(self):
        data = {'data': {'domainQuery': {'apiReseller': {'parent': '1234', 'child': '5678'}}}}
        actual = get_shopper_id_from_dict(data)
        assert_equal(actual, '5678')

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

    def test_get_ssl_subscriptions_from_dict(self):
        data = {'data': {'domainQuery': {'sslSubscriptions': '1234'}}}
        actual = get_ssl_subscriptions_from_dict(data)
        assert_equal(actual, '1234')

    def test_get_kelvin_domain_id_from_dict(self):
        data = {'domain': {'domainId': '1234'}}
        actual = get_kelvin_domain_id_from_dict(data)
        assert_equal(actual, '1234')

    def test_get_kelvin_domain_id_from_dict_none(self):
        data = {'domain': {'brand': 'BRAND'}}
        actual = get_kelvin_domain_id_from_dict(data)
        assert_is_none(actual)

    def test_get_sucuri_product_from_dict(self):
        data = {'data': {'domainQuery': {'securitySubscription': {'sucuriProduct':
                                                                  [self.sucuri_malware_remover_product]}}}}
        actual = get_sucuri_product_from_dict(data)
        assert_equal(actual, [self.sucuri_malware_remover_product])

    def test_sanitize_url(self, url='https://someurl.com/path/to/bad/'):
        sanitized = sanitize_url(url)
        assert_equal('hxxps://someurl.com/path/to/bad/', sanitized)

    def test_sanitize_url_with_email(self, url='https://anotherurl.xyz/?email=reporter@domain.biz'):
        sanitized = sanitize_url(url)
        assert_equal('hxxps://anotherurl.xyz/?email=redacted@redacted.tld', sanitized)
