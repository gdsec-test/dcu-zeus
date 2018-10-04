from mockredis import mock_redis_client
from nose.tools import assert_false, assert_true

from zeus.persist.notification_timeouts import Throttle


class TestPersist:
    @classmethod
    def setup(cls):
        cls._persist = Throttle('0.0.0.0', 1)
        cls._persist.redis = mock_redis_client(host='0.0.0.0', port=6379, db=0)
        cls._domain = 'google.com'
        cls._shopper_id = 'test-id'
        cls._guid = 'test-guid'

    def test_key_exists(self):
        assert_false(self._persist.key_exists(self._domain))

        self._persist.set_key(self._domain)
        assert_true(self._persist.key_exists(self._domain))

    def test_can_shopper_email_be_sent(self):
        assert_true(self._persist.can_shopper_email_be_sent(self._shopper_id))

        self._persist.set_key(self._shopper_id)
        assert_false(self._persist.can_shopper_email_be_sent(self._shopper_id))

    def test_can_fraud_email_be_sent(self):
        assert_true(self._persist.can_fraud_email_be_sent(self._domain))

        self._persist.set_key(self._domain)
        assert_false(self._persist.can_fraud_email_be_sent(self._domain))

    def test_can_suspend_hosting_product(self):
        assert_true(self._persist.can_suspend_hosting_product(self._guid))

        self._persist.set_key(self._guid)
        assert_false(self._persist.can_suspend_hosting_product(self._guid))

    def test_can_suspend_domain(self):
        assert_true(self._persist.can_suspend_domain(self._domain))

        self._persist.set_key(self._domain)
        assert_false(self._persist.can_suspend_domain(self._domain))

    def test_can_crm_be_notated(self):
        assert_true(self._persist.can_crm_be_notated(self._shopper_id))

        self._persist.set_key(self._shopper_id)
        assert_false(self._persist.can_crm_be_notated(self._shopper_id))

    def test_can_slack_message_be_sent(self):
        key = 'slack-key'
        assert_true(self._persist.can_slack_message_be_sent(key))

        self._persist.set_key(key)
        assert_false(self._persist.can_slack_message_be_sent(key))
