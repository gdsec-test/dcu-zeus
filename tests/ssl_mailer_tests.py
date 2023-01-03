import logging
from unittest import TestCase

import mongomock
from hermes.exceptions import InvalidEmailRecipientException
from mock import patch
from mockredis import mock_redis_client

import mongohandler as handler
from mongohandler import MongoLogFactory
from settings import UnitTestConfig
from zeus.events.email.ssl_mailer import SSLMailer
from zeus.events.user_logging.user_logger import UEVENT
from zeus.persist.notification_timeouts import Throttle


class TestSSLMailer(TestCase):

    def setUp(self):
        self._mailer = SSLMailer(UnitTestConfig)
        self._mailer._throttle = self._persist = Throttle('0.0.0.0', 1)
        self._persist.redis = mock_redis_client(host='0.0.0.0', port=6379, db=0)
        self._connection = mongomock.MongoClient()
        self._collection = self._connection.logs
        handler._connection = self._connection
        logging.basicConfig()
        logging.getLogger().addHandler(MongoLogFactory(level=UEVENT, basic_config=True))

    @patch('zeus.events.email.ssl_mailer.send_mail', return_value='SUCCESS')
    def test_send_ssl_revocation_success(self, send_mail):
        self.assertTrue(self._mailer.send_revocation_email('DCU123', 'abc.com', '1234', [{'certCommonName': '*.abc.com', 'certType': 'SSL Cert', 'createdAt': '2010-10-27', 'expiresAt': '2019-10-28'}, {'certCommonName': 'subdomain.abc.com', 'certType': 'Wildcard SSL Cert', 'createdAt': '2010-10-27', 'expiresAt': '2019-10-28'}]))

    @patch('zeus.events.email.ssl_mailer.send_mail', side_effect=InvalidEmailRecipientException())
    def test_send_ssl_revocation_invalid_recipient_exception(self, send_mail):
        self.assertFalse(self._mailer.send_revocation_email('DCU123', 'abc.com', '1234', [{'certCommonName': '*.abc.com', 'certType': 'SSL Cert', 'createdAt': '2010-10-27', 'expiresAt': '2019-10-28'}]))

    def test_handle_ssl_certs_invalid_request(self):
        self.assertFalse(self._mailer.send_revocation_email('DCU123', None, None, None))
