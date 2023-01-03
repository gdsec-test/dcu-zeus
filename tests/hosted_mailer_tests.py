import logging
from unittest import TestCase

import mongomock
from hermes.exceptions import OCMException
from mock import patch
from mockredis import mock_redis_client

import mongohandler as handler
from mongohandler import MongoLogFactory
from settings import UnitTestConfig
from zeus.events.email.hosted_mailer import HostedMailer
from zeus.events.user_logging.user_logger import UEVENT
from zeus.persist.notification_timeouts import Throttle


class TestRegisteredMailer(TestCase):
    def setUp(self):
        self._mailer = HostedMailer(UnitTestConfig)
        self._mailer._throttle = self._persist = Throttle('0.0.0.0', 1)
        self._persist.redis = mock_redis_client(host='0.0.0.0', port=6379, db=0)
        self._connection = mongomock.MongoClient()
        self._collection = self._connection.logs.logs
        handler._connection = self._connection
        logging.basicConfig()
        logging.getLogger().addHandler(MongoLogFactory(level=UEVENT, basic_config=True))

    ''' Hosted Warning Tests '''

    @patch('zeus.events.email.hosted_mailer.send_mail')
    def test_send_hosted_warning(self, send_mail):
        self.assertTrue(self._mailer.send_hosted_warning(None, None, 'test-id', 'source'))

    @patch('zeus.events.email.hosted_mailer.send_mail', side_effect=OCMException())
    def test_send_hosted_warning_exception(self, send_mail):
        self.assertFalse(self._mailer.send_hosted_warning(None, None, 'test-id', None))

    @patch('zeus.events.email.hosted_mailer.send_mail')
    def test_send_sucuri_hosted_warning(self, send_mail):
        self.assertTrue(self._mailer.send_sucuri_hosted_warning(None, None, 'test-id', 'source'))

    @patch('zeus.events.email.hosted_mailer.send_mail', side_effect=OCMException())
    def test_send_sucuri_hosted_warning_exception(self, send_mail):
        self.assertFalse(self._mailer.send_sucuri_hosted_warning(None, None, 'test-id', None))

    ''' Content Removed Tests '''

    @patch('zeus.events.email.hosted_mailer.send_mail')
    def test_send_content_removed(self, send_mail):
        self.assertTrue(self._mailer.send_content_removed('test-ticket', 'test-domain', 'test-id'))

    @patch('zeus.events.email.hosted_mailer.send_mail', side_effect=OCMException())
    def test_send_content_removed_exception(self, send_mail):
        self.assertFalse(self._mailer.send_content_removed('test-ticket', 'test-domain', 'test-id'))

    ''' Hosted Suspension Tests '''

    @patch('zeus.events.email.hosted_mailer.send_mail')
    def test_send_shopper_hosted_suspension(self, send_mail):
        self.assertTrue(self._mailer.send_shopper_hosted_suspension(None, None, 'test-id', 'source'))

    @patch('zeus.events.email.hosted_mailer.send_mail', side_effect=OCMException())
    def test_send_shopper_hosted_suspension_exception(self, send_mail):
        self.assertFalse(self._mailer.send_shopper_hosted_suspension(None, None, 'test-id', None))

    ''' CSAM Hosted Suspension Tests '''

    @patch('zeus.events.email.hosted_mailer.send_mail')
    def test_send_csam_hosted_suspension(self, send_mail):
        self.assertTrue(self._mailer.send_csam_hosted_suspension(None, None, 'test-id'))

    ''' Intentional Hosted Suspension Tests '''

    @patch('zeus.events.email.hosted_mailer.send_mail')
    def test_send_shopper_hosted_intentional_suspension(self, send_mail):
        self.assertTrue(self._mailer.send_shopper_hosted_intentional_suspension(None, None, 'test-id', None))

    @patch('zeus.events.email.hosted_mailer.send_mail', side_effect=OCMException())
    def test_send_shopper_hosted_intentional_suspension_exception(self, send_mail):
        self.assertFalse(self._mailer.send_shopper_hosted_intentional_suspension(None, None, 'test-id', None))

    ''' Shopper Compromise Hosted Suspension Tests '''

    @patch('zeus.events.email.hosted_mailer.send_mail')
    def test_send_shopper_compromise_hosted_suspension(self, send_mail):
        self.assertTrue(self._mailer.send_shopper_compromise_hosted_suspension(None, None, 'test-id'))

    @patch('zeus.events.email.hosted_mailer.send_mail', side_effect=OCMException())
    def test_send_shopper_compromise_hosted_suspension_exception(self, send_mail):
        self.assertFalse(self._mailer.send_shopper_compromise_hosted_suspension(None, None, 'test-id'))

    ''' Shopper Extensive Compromise Hosted Suspension Tests '''

    @patch('zeus.events.email.hosted_mailer.send_mail')
    def test_send_extensive_compromise_suspension(self, send_mail):
        self.assertTrue(self._mailer.send_extensive_compromise(None, None, 'test-id'))

    @patch('zeus.events.email.hosted_mailer.send_mail', side_effect=OCMException())
    def test_send_extensive_compromise_suspension_exception(self, send_mail):
        self.assertFalse(self._mailer.send_extensive_compromise(None, None, 'test-id'))
