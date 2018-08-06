import logging

import mongomock
from hermes.exceptions import OCMException
from mock import patch
from nose.tools import assert_false, assert_true

import mongohandler as handler
from mongohandler import MongoLogFactory
from settings import TestingConfig
from zeus.events.email.foreign_mailer import ForeignMailer
from zeus.events.user_logging.user_logger import UEVENT


class TestForeignMailer:
    @classmethod
    def setup(cls):
        cls._mailer = ForeignMailer(TestingConfig)
        cls._connection = mongomock.MongoClient()
        cls._collection = cls._connection.logs.logs
        handler._connection = cls._connection
        logging.basicConfig()
        logging.getLogger().addHandler(MongoLogFactory(level=UEVENT, basic_config=True))

    @patch('zeus.events.email.foreign_mailer.send_mail', return_value={})
    def test_send_hosting_provider_notice(self, send_mail):
        assert_true(self._mailer.send_foreign_hosting_notice(None, None, 'test-source', 'FOREIGN', ['noc@'], None))

    def test_send_hosting_provider_notice_invalid_hosting_brand(self):
        assert_false(self._mailer.send_foreign_hosting_notice(None, None, None, 'GODADDY', [], None))

    def test_send_hosting_provider_notice_no_shoppers(self):
        assert_false(self._mailer.send_foreign_hosting_notice(None, None, None, 'FOREIGN', [], None))

    @patch('hermes.messenger.send_mail', side_effect=OCMException())
    def test_send_hosting_provider_notice_exception(self, send_mail):
        assert_false(self._mailer.send_foreign_hosting_notice(None, None, None, 'FOREIGN', ['test-id'], None))
