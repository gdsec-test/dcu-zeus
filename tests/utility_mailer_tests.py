import logging
from unittest import TestCase

import mongomock
from hermes.exceptions import OCMException
from mock import patch
from mockredis import mock_redis_client

import mongohandler as handler
from mongohandler import MongoLogFactory
from settings import UnitTestConfig
from zeus.events.email.utility_mailer import UtilityMailer
from zeus.events.user_logging.user_logger import UEVENT
from zeus.persist.notification_timeouts import Throttle


class TestUtilityMailer(TestCase):
    def setUp(self):
        self._mailer = UtilityMailer(UnitTestConfig)
        self._mailer._throttle = self._persist = Throttle('0.0.0.0', 1)
        self._persist.redis = mock_redis_client(host='0.0.0.0', port=6379, db=0)
        self._connection = mongomock.MongoClient()
        self._collection = self._connection.logs.logs
        handler._connection = self._connection
        logging.basicConfig()
        logging.getLogger().addHandler(MongoLogFactory(level=UEVENT, basic_config=True))

    @patch('zeus.events.email.utility_mailer.send_mail')
    def test_send_account_compromised_email(self, send_mail):
        self.assertTrue(self._mailer.send_account_compromised_email(None))

    @patch('zeus.events.email.utility_mailer.send_mail', side_effect=OCMException())
    def test_send_account_compromised_email_exception(self, send_mail):
        self.assertFalse(self._mailer.send_account_compromised_email(None))

    @patch('zeus.events.email.utility_mailer.send_mail')
    def test_send_pci_compliance_violation(self, send_mail):
        self.assertTrue(self._mailer.send_pci_compliance_violation(None, None))

    @patch('zeus.events.email.utility_mailer.send_mail', side_effect=OCMException())
    def test_send_pci_compliance_violation_exception(self, send_mail):
        self.assertFalse(self._mailer.send_pci_compliance_violation(None, None))
