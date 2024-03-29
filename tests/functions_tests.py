from unittest import TestCase

from zeus.utils.functions import (get_domain_create_date_from_dict,
                                  get_high_value_domain_from_dict,
                                  get_host_abuse_email_from_dict,
                                  get_host_brand_from_dict,
                                  get_kelvin_domain_id_from_dict,
                                  get_parent_child_shopper_ids_from_dict,
                                  get_shopper_create_date_from_dict,
                                  get_ssl_subscriptions_from_dict,
                                  get_sucuri_product_from_dict, sanitize_url)


class TestFunctions(TestCase):
    sucuri_malware_remover_product = 'Website Security Deluxe'

    def test_get_parent_child_shopper_ids_from_dict_none(self):
        actual = get_parent_child_shopper_ids_from_dict(None)
        self.assertIsNone(actual)

    def test_get_parent_child_shopper_ids_from_dict_no_parent(self):
        data = {'data': {'domainQuery': {'apiReseller': {'parent': None, 'child': '5678'}}}}
        actual = get_parent_child_shopper_ids_from_dict(data)
        self.assertIsNone(actual)

    def test_get_parent_child_shopper_ids_from_dict(self):
        data = {'data': {'domainQuery': {'apiReseller': {'parent': '1234', 'child': '5678'}}}}
        actual = get_parent_child_shopper_ids_from_dict(data)
        self.assertEqual(actual, {'parent_shopper_id': '1234', 'child_shopper_id': '5678',
                                  'parent_customer_id': None, 'child_customer_id': None})

    def test_get_parent_child_customer_ids_from_dict(self):
        data = {'data': {'domainQuery': {'apiReseller': {'parent': '1234', 'child': '5678',
                                                         'parentCustomerId': 'abc', 'childCustomerId': 'def'}}}}
        actual = get_parent_child_shopper_ids_from_dict(data)
        self.assertEqual(actual, {'parent_shopper_id': '1234', 'child_shopper_id': '5678',
                                  'parent_customer_id': 'abc', 'child_customer_id': 'def'})

    def test_get_domain_create_date_from_dict_none(self):
        actual = get_domain_create_date_from_dict(None)
        self.assertIsNone(actual)

    def test_get_domain_create_date_from_dict(self):
        data = {'data': {'domainQuery': {'registrar': {'domainCreateDate': 'Jan 1, 1970'}}}}
        actual = get_domain_create_date_from_dict(data)
        self.assertEqual(actual, 'Jan 1, 1970')

    def test_get_shopper_create_date_from_dict_none(self):
        actual = get_shopper_create_date_from_dict(None)
        self.assertIsNone(actual)

    def test_get_shopper_create_date_from_dict(self):
        data = {'data': {'domainQuery': {'shopperInfo': {'shopperCreateDate': 'Jan 1, 1970'}}}}
        actual = get_shopper_create_date_from_dict(data)
        self.assertEqual(actual, 'Jan 1, 1970')

    def test_get_host_abuse_email_from_dict_none(self):
        actual = get_host_abuse_email_from_dict(None)
        self.assertEqual(actual, [])

    def test_get_host_abuse_email_from_dict_none2(self):
        data = {'data': {'domainQuery': {'host': {'hostingAbuseEmail': None}}}}
        actual = get_host_abuse_email_from_dict(data)
        self.assertEqual(actual, [])

    def test_get_host_abuse_email_from_dict_single(self):
        data = {'data': {'domainQuery': {'host': {'hostingAbuseEmail': 'xxx@xxx.com'}}}}
        actual = get_host_abuse_email_from_dict(data)
        self.assertEqual(actual, ['xxx@xxx.com'])

    def test_get_host_abuse_email_from_dict_list_abuse(self):
        data = {'data': {'domainQuery': {'host': {'hostingAbuseEmail': ['abuse@xxx.com']}}}}
        actual = get_host_abuse_email_from_dict(data)
        self.assertEqual(actual, ['abuse@xxx.com'])

    def test_get_host_abuse_email_from_dict_list_non_abuse(self):
        data = {'data': {'domainQuery': {'host': {'hostingAbuseEmail': ['xxx@xxx.com']}}}}
        actual = get_host_abuse_email_from_dict(data)
        self.assertEqual(actual, ['xxx@xxx.com'])

    def test_get_host_brand_from_dict_none(self):
        actual = get_host_brand_from_dict(None)
        self.assertIsNone(actual)

    def test_get_host_brand_from_dict(self):
        data = {'data': {'domainQuery': {'host': {'brand': 'GODADDY'}}}}
        actual = get_host_brand_from_dict(data)
        self.assertEqual(actual, 'GODADDY')

    def test_get_shopper_create_date_none(self):
        actual = get_shopper_create_date_from_dict(None)
        self.assertIsNone(actual)

    def test_get_shopper_create_date(self):
        data = {'data': {'domainQuery': {'shopperInfo': {'shopperCreateDate': '1 Jan, 1970'}}}}
        actual = get_shopper_create_date_from_dict(data)
        self.assertEqual(actual, '1 Jan, 1970')

    def test_get_ssl_subscriptions_from_dict(self):
        data = {'data': {'domainQuery': {'sslSubscriptions': '1234'}}}
        actual = get_ssl_subscriptions_from_dict(data)
        self.assertEqual(actual, '1234')

    def test_get_kelvin_domain_id_from_dict(self):
        data = {'domain': {'domainId': '1234'}}
        actual = get_kelvin_domain_id_from_dict(data)
        self.assertEqual(actual, '1234')

    def test_get_kelvin_domain_id_from_dict_none(self):
        data = {'domain': {'brand': 'BRAND'}}
        actual = get_kelvin_domain_id_from_dict(data)
        self.assertIsNone(actual)

    def test_get_sucuri_product_from_dict(self):
        data = {'data': {'domainQuery': {'securitySubscription': {'sucuriProduct':
                                                                  [self.sucuri_malware_remover_product]}}}}
        actual = get_sucuri_product_from_dict(data)
        self.assertEqual(actual, [self.sucuri_malware_remover_product])

    def test_sanitize_url(self, url='https://someurl.com/path/to/bad/'):
        sanitized = sanitize_url(url)
        self.assertEqual('hxxps://someurl.com/path/to/bad/', sanitized)

    def test_sanitize_url_with_email(self, url='https://anotherurl.xyz/?email=reporter@domain.biz'):
        sanitized = sanitize_url(url)
        self.assertEqual('hxxps://anotherurl.xyz/?email=redacted@redacted.tld', sanitized)

    def test_get_high_value_domain_from_dict(self):
        data = {'data': {'domainQuery': {'isDomainHighValue': True}}}
        actual = get_high_value_domain_from_dict(data)
        self.assertEqual(actual, True)
