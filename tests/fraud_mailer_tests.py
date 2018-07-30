import logging

import mongomock
from hermes.exceptions import OCMException
from mock import patch
from mockredis import mock_redis_client
from nose.tools import assert_false, assert_true

import mongohandler as handler
from mongohandler import MongoLogFactory
from settings import TestingConfig
from zeus.events.email.fraud_mailer import FraudMailer
from zeus.events.user_logging.user_logger import UEVENT
from zeus.persist.persist import Persist


class TestFraudMailer:
    @classmethod
    def setup(cls):
        cls._mailer = FraudMailer(TestingConfig)
        cls._mailer._throttle = cls._persist = Persist('0.0.0.0', 1)
        cls._persist.redis = mock_redis_client(host='0.0.0.0', port=6379, db=0)
        cls._connection = mongomock.MongoClient()
        cls._collection = cls._connection.logs.logs
        handler._connection = cls._connection
        logging.basicConfig()
        logging.getLogger().addHandler(MongoLogFactory(level=UEVENT, basic_config=True))

    ''' New Domain Tests '''

    @patch('zeus.events.email.fraud_mailer.send_mail', return_value={})
    def test_send_fraud_new_domain_notification(self, send_mail):
        assert_true(self._mailer.send_new_domain_notification(None, None, None, None, None, 'test-source', None))

    @patch('hermes.messenger.send_mail', side_effect=OCMException())
    def test_send_fraud_new_domain_notification_exception(self, send_mail):
        assert_false(self._mailer.send_new_domain_notification(None, None, None, None, None, 'test-source', None))

    ''' New Shopper Tests '''

    @patch('zeus.events.email.fraud_mailer.send_mail', return_value={})
    def test_send_fraud_new_shopper_notification(self, send_mail):
        assert_true(self._mailer.send_new_shopper_notification(None, None, None, None, None, 'test-source', None))

    @patch('hermes.messenger.send_mail', side_effect=OCMException())
    def test_send_fraud_new_shopper_notification_exception(self, send_mail):
        assert_false(self._mailer.send_new_shopper_notification(None, None, None, None, None, 'test-source', None))

    ''' Malicious Notification Tests '''

    @patch('zeus.events.email.fraud_mailer.send_mail', return_value={})
    def test_send_malicious_notification(self, send_mail):
        assert_true(self._mailer.send_malicious_domain_notification(None, None, None, None, 'test-source', None))

    @patch('hermes.messenger.send_mail', side_effect=OCMException())
    def test_send_malicious_notification_exception(self, send_mail):
        assert_false(self._mailer.send_malicious_domain_notification(None, None, None, None, 'test-source', None))

    ''' New Hosting Account Tests '''

    @patch('zeus.events.email.fraud_mailer.send_mail', return_value={})
    def test_send_new_hosting_account_notification(self, send_mail):
        assert_true(self._mailer.send_new_hosting_account_notification(None, None, None, None, None, 'test-source', None))

    @patch('hermes.messenger.send_mail', side_effect=OCMException())
    def test_send_new_hosting_account_notification_exception(self, send_mail):
        assert_false(self._mailer.send_new_hosting_account_notification(None, None, None, None, None, 'test-source', None))

    ''' Malicious Hosting Notification '''

    @patch('zeus.events.email.fraud_mailer.send_mail', return_value={})
    def test_send_malicious_hosting_notification(self, send_mail):
        assert_true(self._mailer.send_malicious_hosting_notification(None, None, None, None, 'test-source', None, None))

    @patch('hermes.messenger.send_mail', side_effect=OCMException())
    def test_send_malicious_hosting_notification_exception(self, send_mail):
        assert_false(self._mailer.send_malicious_hosting_notification(None, None, None, None, 'test-source', None, None))
