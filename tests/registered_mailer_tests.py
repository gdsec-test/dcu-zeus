import logging

import mongomock
from hermes.exceptions import OCMException
from mock import patch
from mockredis import mock_redis_client
from nose.tools import assert_false, assert_true

import mongohandler as handler
from mongohandler import MongoLogFactory
from settings import TestingConfig
from zeus.events.email.registered_mailer import RegisteredMailer
from zeus.events.user_logging.user_logger import UEVENT
from zeus.persist.persist import Persist


class TestRegisteredMailer:
    @classmethod
    def setup(cls):
        cls._mailer = RegisteredMailer(TestingConfig)
        cls._mailer._throttle = cls._persist = Persist('0.0.0.0', 1)
        cls._persist.redis = mock_redis_client(host='0.0.0.0', port=6379, db=0)
        cls._connection = mongomock.MongoClient()
        cls._collection = cls._connection.logs.logs
        handler._connection = cls._connection
        logging.basicConfig()
        logging.getLogger().addHandler(MongoLogFactory(level=UEVENT, basic_config=True))

    ''' Registrant Warning Tests '''

    @patch('zeus.events.email.registered_mailer.send_mail')
    def test_send_registrant_warning(self, send_mail):
        send_mail.return_value = {}
        assert_true(self._mailer.send_registrant_warning('test-ticket', 'test-domain', ['test-id'], 'test-source'))

    def test_send_registrant_warning_no_shoppers(self):
        assert_false(self._mailer.send_registrant_warning(None, None, [], None))

    @patch('hermes.messenger.send_mail')
    def test_send_registrant_warning_exception(self, send_mail):
        send_mail.side_effect = OCMException()
        assert_false(self._mailer.send_registrant_warning(None, None, ['test-id'], None))

    ''' Shoper Suspension Tests '''

    @patch('zeus.events.email.registered_mailer.send_mail')
    def test_send_shopper_suspension(self, send_mail):
        send_mail.return_value = {}
        assert_true(
            self._mailer.send_shopper_suspension('test-ticket', 'test-domain', ['test-id'], 'test-source', 'PHISHING'))

    def test_send_shopper_suspension_no_shoppers(self):
        assert_false(self._mailer.send_shopper_suspension(None, None, [], None, None))

    @patch('hermes.messenger.send_mail')
    def test_send_shopper_suspension_exception(self, send_mail):
        send_mail.side_effect = OCMException()
        assert_false(self._mailer.send_shopper_suspension(None, None, ['test-id'], None, None))

    ''' Shopper Intentional Suspension Tests '''

    @patch('zeus.events.email.registered_mailer.send_mail')
    def test_send_shopper_intentional_suspension(self, send_mail):
        send_mail.return_value = {}
        assert_true(self._mailer.send_shopper_intentional_suspension(None, None, ['test-id'], 'PHISHING'))

    def test_send_shopper_intentional_suspension_no_shoppers(self):
        assert_false(self._mailer.send_shopper_intentional_suspension(None, None, [], None))

    @patch('hermes.messenger.send_mail')
    def test_send_shopper_intentional_suspension_exception(self, send_mail):
        send_mail.side_effect = OCMException()
        assert_false(self._mailer.send_shopper_intentional_suspension(None, None, ['test-id'], None))

    ''' 3rd Party Hosting Provider Tests '''

    @patch('zeus.events.email.registered_mailer.send_mail')
    def test_send_hosting_provider_notice(self, send_mail):
        send_mail.return_value = {}
        assert_true(self._mailer.send_hosting_provider_notice(None, None, 'test-source', 'FOREIGN', ['noc@'], None))

    def test_send_hosting_provider_notice_invalid_hosting_brand(self):
        assert_false(self._mailer.send_hosting_provider_notice(None, None, None, 'GODADDY', [], None))

    def test_send_hosting_provider_notice_no_shoppers(self):
        assert_false(self._mailer.send_hosting_provider_notice(None, None, None, 'FOREIGN', [], None))

    @patch('hermes.messenger.send_mail')
    def test_send_hosting_provider_notice_exception(self, send_mail):
        send_mail.side_effect = OCMException()
        assert_false(self._mailer.send_hosting_provider_notice(None, None, None, 'FOREIGN', ['test-id'], None))
