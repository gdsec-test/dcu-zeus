import logging

import mongomock
from hermes.exceptions import OCMException
from mock import patch
from mockredis import mock_redis_client
from nose.tools import assert_false, assert_true

import mongohandler as handler
from mongohandler import MongoLogFactory
from settings import TestingConfig
from zeus.events.email.utility_mailer import UtilityMailer
from zeus.events.user_logging.user_logger import UEVENT
from zeus.persist.notification_timeouts import Throttle


class TestUtilityMailer:
    @classmethod
    def setup(cls):
        cls._mailer = UtilityMailer(TestingConfig)
        cls._mailer._throttle = cls._persist = Throttle('0.0.0.0', 1)
        cls._persist.redis = mock_redis_client(host='0.0.0.0', port=6379, db=0)
        cls._connection = mongomock.MongoClient()
        cls._collection = cls._connection.logs.logs
        handler._connection = cls._connection
        logging.basicConfig()
        logging.getLogger().addHandler(MongoLogFactory(level=UEVENT, basic_config=True))

    @patch('zeus.events.email.utility_mailer.send_mail')
    def test_send_account_compromised_email(self, send_mail):
        assert_true(self._mailer.send_account_compromised_email(None))

    @patch('zeus.events.email.utility_mailer.send_mail', side_effect=OCMException())
    def test_send_account_compromised_email_exception(self, send_mail):
        assert_false(self._mailer.send_account_compromised_email(None))

    @patch('zeus.events.email.utility_mailer.send_mail')
    def test_send_pci_compliance_violation(self, send_mail):
        assert_true(self._mailer.send_pci_compliance_violation(None, None))

    @patch('zeus.events.email.utility_mailer.send_mail', side_effect=OCMException())
    def test_send_pci_compliance_violation_exception(self, send_mail):
        assert_false(self._mailer.send_pci_compliance_violation(None, None))
