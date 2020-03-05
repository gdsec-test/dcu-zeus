import logging

import mongomock
from hermes.exceptions import InvalidEmailRecipientException
from mock import patch
from mockredis import mock_redis_client
from nose.tools import assert_false, assert_true

import mongohandler as handler
from mongohandler import MongoLogFactory
from settings import TestingConfig
from zeus.events.email.oceo_mailer import OCEOMailer
from zeus.events.user_logging.user_logger import UEVENT
from zeus.persist.notification_timeouts import Throttle


class TestOCEOMailer:

    @classmethod
    def setup(cls):
        cls._mailer = OCEOMailer(TestingConfig)
        cls._mailer._throttle = cls._persist = Throttle('0.0.0.0', 1)
        cls._persist.redis = mock_redis_client(host='0.0.0.0', port=6379, db=0)
        cls._connection = mongomock.MongoClient()
        cls._collection = cls._connection.logs
        handler._connection = cls._connection
        logging.basicConfig()
        logging.getLogger().addHandler(MongoLogFactory(level=UEVENT, basic_config=True))

    @patch('zeus.events.email.oceo_mailer.send_mail', return_value='SUCCESS')
    def test_send_termination_success(self, send_mail):
        assert_true(self._mailer.send_termination_email('DCU123', '1234', 'abc.com', 'PHISHING'))

    @patch('zeus.events.email.oceo_mailer.send_mail', side_effect=InvalidEmailRecipientException())
    def test_send_termination_invalid_recipient_exception(self, send_mail):
        assert_false(self._mailer.send_termination_email('DCU123', '1234', 'abc.com', 'PHISHING'))
