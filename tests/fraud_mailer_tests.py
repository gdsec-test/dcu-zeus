import logging
from unittest import TestCase

import mongomock
from hermes.exceptions import SMTPException
from mock import patch
from mockredis import mock_redis_client

import mongohandler as handler
from mongohandler import MongoLogFactory
from settings import UnitTestConfig
from zeus.events.email.fraud_mailer import FraudMailer
from zeus.events.user_logging.user_logger import UEVENT
from zeus.persist.notification_timeouts import Throttle


class TestFraudMailer(TestCase):
    def setUp(self):
        self._mailer = FraudMailer(UnitTestConfig)
        self._mailer._throttle = self._persist = Throttle('0.0.0.0', 1)
        self._persist.redis = mock_redis_client(host='0.0.0.0', port=6379, db=0)
        self._connection = mongomock.MongoClient()
        self._collection = self._connection.logs.logs
        handler._connection = self._connection
        logging.basicConfig()
        logging.getLogger().addHandler(MongoLogFactory(level=UEVENT, basic_config=True))

    ''' New Domain Tests '''

    @patch('zeus.events.email.fraud_mailer.send_mail', return_value='SUCCESS')
    def test_send_fraud_new_domain_notification(self, send_mail):
        self.assertTrue(self._mailer.send_new_domain_notification(None, None, None, None, None, 'test-source', None))

    @patch('zeus.events.email.fraud_mailer.send_mail', side_effect=SMTPException())
    def test_send_fraud_new_domain_notification_exception(self, send_mail):
        self.assertFalse(self._mailer.send_new_domain_notification(None, None, None, None, None, 'test-source', None))

    ''' New Shopper Tests '''

    @patch('zeus.events.email.fraud_mailer.send_mail', return_value='SUCCESS')
    def test_send_fraud_new_shopper_notification(self, send_mail):
        self.assertTrue(self._mailer.send_new_shopper_notification(None, None, None, None, None, 'test-source', None))

    @patch('zeus.events.email.fraud_mailer.send_mail', side_effect=SMTPException())
    def test_send_fraud_new_shopper_notification_exception(self, send_mail):
        self.assertFalse(self._mailer.send_new_shopper_notification(None, None, None, None, None, 'test-source', None))

    ''' Malicious Notification Tests '''

    @patch('zeus.events.email.fraud_mailer.send_mail', return_value='SUCCESS')
    def test_send_malicious_notification(self, send_mail):
        self.assertTrue(self._mailer.send_malicious_domain_notification(None, None, None, None, 'test-source', None))

    @patch('zeus.events.email.fraud_mailer.send_mail', side_effect=SMTPException())
    def test_send_malicious_notification_exception(self, send_mail):
        self.assertFalse(self._mailer.send_malicious_domain_notification(None, None, None, None, 'test-source', None))

    ''' Shopper Compromise Domain Notification Tests '''

    @patch('zeus.events.email.fraud_mailer.send_mail', return_value='SUCCESS')
    def test_send_compromise_notification(self, send_mail):
        self.assertTrue(self._mailer.send_compromise_domain_notification(None, None, None, None, 'test-source', None))

    @patch('zeus.events.email.fraud_mailer.send_mail', side_effect=SMTPException())
    def test_send_compromise_notification_exception(self, send_mail):
        self.assertFalse(self._mailer.send_compromise_domain_notification(None, None, None, None, 'test-source', None))

    ''' New Hosting Account Tests '''

    @patch('zeus.events.email.fraud_mailer.send_mail', return_value='SUCCESS')
    def test_send_new_hosting_account_notification(self, send_mail):
        self.assertTrue(self._mailer.send_new_hosting_account_notification(None, None, None, None, None, 'test-source', None))

    @patch('zeus.events.email.fraud_mailer.send_mail', side_effect=SMTPException())
    def test_send_new_hosting_account_notification_exception(self, send_mail):
        self.assertFalse(self._mailer.send_new_hosting_account_notification(None, None, None, None, None, 'test-source', None))

    ''' Malicious Hosting Notification '''

    @patch('zeus.events.email.fraud_mailer.send_mail', return_value='SUCCESS')
    def test_send_malicious_hosting_notification(self, send_mail):
        self.assertTrue(self._mailer.send_malicious_hosting_notification(None, None, None, None, 'test-source', None, None))

    @patch('zeus.events.email.fraud_mailer.send_mail', side_effect=SMTPException())
    def test_send_malicious_hosting_notification_exception(self, send_mail):
        self.assertFalse(self._mailer.send_malicious_hosting_notification(None, None, None, None, 'test-source', None, None))

    ''' Shopper Compromise Hosting Notification '''

    @patch('zeus.events.email.fraud_mailer.send_mail', return_value='SUCCESS')
    def test_send_compromise_hosting_notification(self, send_mail):
        self.assertTrue(self._mailer.send_compromise_hosting_notification(None, None, None, None, 'test-source', None, None))

    @patch('zeus.events.email.fraud_mailer.send_mail', side_effect=SMTPException())
    def test_send_compromise_hosting_notification_exception(self, send_mail):
        self.assertFalse(self._mailer.send_compromise_hosting_notification(None, None, None, None, 'test-source', None, None))
