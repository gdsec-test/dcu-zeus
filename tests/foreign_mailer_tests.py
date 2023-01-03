import logging
from unittest import TestCase

import mongomock
from hermes.exceptions import OCMException
from mock import patch

import mongohandler as handler
from mongohandler import MongoLogFactory
from settings import UnitTestConfig
from zeus.events.email.foreign_mailer import ForeignMailer
from zeus.events.user_logging.user_logger import UEVENT


class TestForeignMailer(TestCase):
    def setUp(self):
        self._mailer = ForeignMailer(UnitTestConfig)
        self._connection = mongomock.MongoClient()
        self._collection = self._connection.logs.logs
        handler._connection = self._connection
        logging.basicConfig()
        logging.getLogger().addHandler(MongoLogFactory(level=UEVENT, basic_config=True))

    @patch('zeus.events.email.foreign_mailer.send_mail', return_value={})
    def test_send_hosting_provider_notice(self, send_mail):
        self.assertTrue(self._mailer.send_foreign_hosting_notice(None, None, 'test-source', 'FOREIGN', ['noc@'], None))

    def test_send_hosting_provider_notice_invalid_hosting_brand(self):
        self.assertFalse(self._mailer.send_foreign_hosting_notice(None, None, None, 'GODADDY', [], None))

    def test_send_hosting_provider_notice_no_shoppers(self):
        self.assertFalse(self._mailer.send_foreign_hosting_notice(None, None, None, 'FOREIGN', [], None))

    @patch('hermes.messenger.send_mail', side_effect=OCMException())
    def test_send_hosting_provider_notice_exception(self, send_mail):
        self.assertFalse(self._mailer.send_foreign_hosting_notice(None, None, None, 'FOREIGN', ['test-id'], None))
