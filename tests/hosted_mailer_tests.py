import logging

import mongomock
from hermes.exceptions import OCMException
from mock import patch
from mockredis import mock_redis_client
from nose.tools import assert_false, assert_true

import mongohandler as handler
from mongohandler import MongoLogFactory
from settings import TestingConfig
from zeus.events.email.hosted_mailer import HostedMailer
from zeus.events.user_logging.user_logger import UEVENT
from zeus.persist.persist import Persist


class TestRegisteredMailer:
    @classmethod
    def setup(cls):
        cls._mailer = HostedMailer(TestingConfig)
        cls._mailer._throttle = cls._persist = Persist('0.0.0.0', 1)
        cls._persist.redis = mock_redis_client(host='0.0.0.0', port=6379, db=0)
        cls._connection = mongomock.MongoClient()
        cls._collection = cls._connection.logs.logs
        handler._connection = cls._connection
        logging.basicConfig()
        logging.getLogger().addHandler(MongoLogFactory(level=UEVENT, basic_config=True))

    ''' Hosted Warning Tests '''

    @patch('zeus.events.email.hosted_mailer.send_mail', return_value={})
    def test_send_hosted_warning(self, send_mail):
        assert_true(self._mailer.send_hosted_warning(None, None, 'test-id', None))

    @patch('hermes.messenger.send_mail', side_effect=OCMException())
    def test_send_hosted_warning_exception(self, send_mail):
        assert_false(self._mailer.send_hosted_warning(None, None, 'test-id', None))

    ''' Content Removed Tests '''

    @patch('zeus.events.email.hosted_mailer.send_mail', return_value={})
    def test_send_content_removed(self, send_mail):
        assert_true(self._mailer.send_content_removed('test-ticket', 'test-domain', 'test-id', 'removed-content'))

    @patch('hermes.messenger.send_mail', side_effect=OCMException())
    def test_send_content_removed_exception(self, send_mail):
        assert_false(self._mailer.send_content_removed('test-ticket', 'test-domain', 'test-id', 'removed-content'))

    ''' Hosted Suspension Tests '''

    @patch('zeus.events.email.hosted_mailer.send_mail', return_value={})
    def test_send_shopper_hosted_suspension(self, send_mail):
        assert_true(self._mailer.send_shopper_hosted_suspension(None, None, 'test-id', None))

    @patch('hermes.messenger.send_mail', side_effect=OCMException())
    def test_send_shopper_hosted_suspension_exception(self, send_mail):
        assert_false(self._mailer.send_shopper_hosted_suspension(None, None, 'test-id', None))

    ''' Intentional Hosted Suspension Tests '''

    @patch('zeus.events.email.hosted_mailer.send_mail', return_value={})
    def test_send_shopper_hosted_intentional_suspension(self, send_mail):
        assert_true(self._mailer.send_shopper_hosted_intentional_suspension(None, None, 'test-id', None))

    @patch('hermes.messenger.send_mail', side_effect=OCMException())
    def test_send_shopper_hosted_intentional_suspension_exception(self, send_mail):
        assert_false(self._mailer.send_shopper_hosted_intentional_suspension(None, None, 'test-id', None))
