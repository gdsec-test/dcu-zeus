from unittest import TestCase

from mockredis import mock_redis_client

from zeus.persist.notification_timeouts import Throttle


class TestPersist(TestCase):
    def setUp(self):
        self._persist = Throttle('0.0.0.0', 1)
        self._persist.redis = mock_redis_client(host='0.0.0.0', port=6379, db=0)
        self._domain = 'google.com'
        self._shopper_id = 'test-id'
        self._guid = 'test-guid'

    def test_key_exists(self):
        self.assertFalse(self._persist.key_exists(self._domain))

        self._persist.set_key(self._domain)
        self.assertTrue(self._persist.key_exists(self._domain))

    def test_can_shopper_email_be_sent(self):
        self.assertTrue(self._persist.can_shopper_email_be_sent(self._shopper_id))

        self._persist.set_key(self._shopper_id)
        self.assertFalse(self._persist.can_shopper_email_be_sent(self._shopper_id))

    def test_can_fraud_email_be_sent(self):
        self.assertTrue(self._persist.can_fraud_email_be_sent(self._shopper_id))

        self._persist.set_key(self._shopper_id)
        self.assertFalse(self._persist.can_fraud_email_be_sent(self._shopper_id))

    def test_can_suspend_hosting_product(self):
        self.assertTrue(self._persist.can_suspend_hosting_product(self._guid))

        self._persist.set_key(self._guid)
        self.assertFalse(self._persist.can_suspend_hosting_product(self._guid))

    def test_can_suspend_domain(self):
        self.assertTrue(self._persist.can_suspend_domain(self._domain))

        self._persist.set_key(self._domain)
        self.assertFalse(self._persist.can_suspend_domain(self._domain))

    def test_can_crm_be_notated(self):
        self.assertTrue(self._persist.can_crm_be_notated(self._domain))

        self._persist.set_key(self._domain)
        self.assertFalse(self._persist.can_crm_be_notated(self._domain))

    def test_can_slack_message_be_sent(self):
        key = 'slack-key'
        self.assertTrue(self._persist.can_slack_message_be_sent(key))

        self._persist.set_key(key)
        self.assertFalse(self._persist.can_slack_message_be_sent(key))

    def test_can_ssl_revocation_email_be_sent(self):
        self.assertTrue(self._persist.can_ssl_revocation_email_be_sent(self._domain))

        self._persist.set_key(self._domain)
        self.assertFalse(self._persist.can_ssl_revocation_email_be_sent(self._domain))
