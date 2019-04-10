import logging

import mongomock
from hermes.exceptions import InvalidEmailRecipientException
from hermes.mailers.interface import SMTP
from mock import patch
from mockredis import mock_redis_client
from nose.tools import assert_false, assert_true

import mongohandler as handler
from mongohandler import MongoLogFactory
from settings import TestingConfig
from zeus.events.email.ssl_mailer import SSLMailer
from zeus.events.user_logging.user_logger import UEVENT
from zeus.persist.notification_timeouts import Throttle


class TestSSLMailer:

    @classmethod
    def setup(cls):
        cls._mailer = SSLMailer(TestingConfig)
        cls._mailer._throttle = cls._persist = Throttle('0.0.0.0', 1)
        cls._persist.redis = mock_redis_client(host='0.0.0.0', port=6379, db=0)
        cls._connection = mongomock.MongoClient()
        cls._collection = cls._connection.logs
        handler._connection = cls._connection
        logging.basicConfig()
        logging.getLogger().addHandler(MongoLogFactory(level=UEVENT, basic_config=True))

    @patch('hermes.mailers.interface.SMTP.send_mail', return_value='SUCCESS')
    def test_send_ssl_revocation_success(self, send_mail):
        assert_true(self._mailer.send_revocation_email('DCU123', 'abc.com', '1234',
                                                       [{'certCommonName': '*.abc.com',
                                                         'certType': 'SSL Cert',
                                                         'createdAt': '2010-10-27',
                                                         'expiresAt': '2019-10-28'},
                                                        {'certCommonName': 'subdomain.abc.com',
                                                         'certType': 'Wildcard SSL Cert',
                                                         'createdAt': '2010-10-27',
                                                         'expiresAt': '2019-10-28'}
                                                        ]))

    @patch.object(SMTP, 'send_mail', side_effect=InvalidEmailRecipientException())
    def test_send_ssl_revocation_invalid_recipient_exception(self, send_mail):
        assert_false(self._mailer.send_revocation_email('DCU123', 'abc.com',
                                                        '1234', [{'certCommonName': '*.abc.com',
                                                                  'certType': 'SSL Cert', 'createdAt': '2010-10-27',
                                                                  'expiresAt': '2019-10-28'}]))

    def test_handle_ssl_certs_invalid_request(self):
        assert_false(self._mailer.send_revocation_email('DCU123', None, None, None))

    def test_handle_ssl_certs_ssl_cert_not_present(self):
        assert_false(self._mailer.send_revocation_email('DCU123', 'abc.com', '1234', []))
