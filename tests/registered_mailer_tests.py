import logging
from unittest import TestCase

import mongomock
from hermes.exceptions import OCMException
from mock import patch
from mockredis import mock_redis_client

import mongohandler as handler
from mongohandler import MongoLogFactory
from settings import UnitTestConfig
from zeus.events.email.registered_mailer import RegisteredMailer
from zeus.events.user_logging.user_logger import UEVENT
from zeus.persist.notification_timeouts import Throttle


class TestRegisteredMailer(TestCase):
    def setUp(self):
        self._mailer = RegisteredMailer(UnitTestConfig)
        self._mailer._throttle = self._persist = Throttle('0.0.0.0', 1)
        self._persist.redis = mock_redis_client(host='0.0.0.0', port=6379, db=0)
        self._connection = mongomock.MongoClient()
        self._collection = self._connection.logs.logs
        handler._connection = self._connection
        logging.basicConfig()
        logging.getLogger().addHandler(MongoLogFactory(level=UEVENT, basic_config=True))

    ''' Registrant Warning Tests '''

    @patch('zeus.events.email.registered_mailer.send_mail')
    @patch('zeus.events.email.registered_mailer.generate_event', return_value={})
    def test_send_user_gen_complaint(self, generate_event, send_mail):
        self.assertTrue(self._mailer.send_user_gen_complaint('test-ticket', 'test-subdomain', 'test-domain-id', ['test-id'],
                                                             'test-source'))

    def test_send_user_gen_complaint_no_shoppers(self):
        self.assertFalse(self._mailer.send_user_gen_complaint(None, None, None, [], None))

    @patch('hermes.messenger.send_mail', side_effect=OCMException())
    @patch('zeus.events.email.registered_mailer.generate_event', return_value={})
    def test_send_user_gen_complaint_exception(self, generate_event, send_mail):
        self.assertFalse(self._mailer.send_user_gen_complaint(None, None, None, ['test-id'], None))

    @patch('zeus.events.email.registered_mailer.send_mail')
    def test_send_registrant_warning(self, send_mail):
        self.assertTrue(self._mailer.send_registrant_warning('test-ticket', 'test-domain', 'test-domain-id', ['test-id'],
                                                             'test-source'))

    def test_send_registrant_warning_no_shoppers(self):
        self.assertFalse(self._mailer.send_registrant_warning(None, None, None, [], None))

    @patch('hermes.messenger.send_mail', side_effect=OCMException())
    def test_send_registrant_warning_exception(self, send_mail):
        self.assertFalse(self._mailer.send_registrant_warning(None, None, None, ['test-id'], None))

    @patch('zeus.events.email.registered_mailer.send_mail')
    def test_send_sucuri_reg_warning(self, send_mail):
        self.assertTrue(self._mailer.send_sucuri_reg_warning('test-ticket', 'test-domain', 'test-domain-id', ['test-id'],
                                                             'test-source'))

    def test_send_send_sucuri_reg_warning_no_shoppers(self):
        self.assertFalse(self._mailer.send_sucuri_reg_warning(None, None, None, [], None))

    @patch('hermes.messenger.send_mail', side_effect=OCMException())
    def test_send_sucuri_reg_warning_exception(self, send_mail):
        self.assertFalse(self._mailer.send_sucuri_reg_warning(None, None, None, ['test-id'], None))

    ''' Shopper Suspension Tests '''

    @patch('zeus.events.email.registered_mailer.send_mail')
    def test_send_shopper_suspension(self, send_mail):
        actual = self._mailer.send_shopper_suspension('test-id', 'test-domain', 'test-domain-id', ['test-id'],
                                                      'test-source', 'PHISHING')
        self.assertTrue(actual)

    def test_send_shopper_suspension_no_shoppers(self):
        self.assertFalse(self._mailer.send_shopper_suspension(None, None, None, [], None, None))

    @patch('hermes.messenger.send_mail', side_effect=OCMException())
    def test_send_shopper_suspension_exception(self, send_mail):
        self.assertFalse(self._mailer.send_shopper_suspension(None, None, None, ['test-id'], None, None))

    ''' CSAM Shopper Suspension test '''

    @patch('zeus.events.email.registered_mailer.send_mail')
    def test_send_csam_shopper_suspension(self, send_mail):
        actual = self._mailer.send_csam_shopper_suspension('test-id', 'test-domain', 'test-shopperid', ['test-id'])
        self.assertTrue(actual)

    ''' Shopper Intentional Suspension Tests '''

    @patch('zeus.events.email.registered_mailer.send_mail')
    def test_send_shopper_intentional_suspension(self, send_mail):
        self.assertTrue(self._mailer.send_shopper_intentional_suspension(None, None, None, ['test-id'], 'PHISHING'))

    def test_send_shopper_intentional_suspension_no_shoppers(self):
        self.assertFalse(self._mailer.send_shopper_intentional_suspension(None, None, None, [], None))

    @patch('hermes.messenger.send_mail', side_efect=OCMException())
    def test_send_shopper_intentional_suspension_exception(self, send_mail):
        self.assertFalse(self._mailer.send_shopper_intentional_suspension(None, None, None, ['test-id'], None))

    ''' Shopper Compromise Suspension Tests '''

    @patch('zeus.events.email.registered_mailer.send_mail')
    def test_send_shopper_compromise_suspension(self, send_mail):
        self.assertTrue(self._mailer.send_shopper_compromise_suspension(None, None, None, ['test-id']))

    def test_send_shopper_compromise_suspension_no_shoppers(self):
        self.assertFalse(self._mailer.send_shopper_compromise_suspension(None, None, None, []))

    @patch('hermes.messenger.send_mail', side_efect=OCMException())
    def test_send_shopper_compromise_suspension_exception(self, send_mail):
        self.assertFalse(self._mailer.send_shopper_compromise_suspension(None, None, None, ['test-id']))

    ''' Repeat Offender Suspension Tests '''

    @patch('zeus.events.email.registered_mailer.send_mail')
    @patch('zeus.events.email.registered_mailer.generate_event', return_value=None)
    def test_send_repeat_offender_suspension(self, generate_event, send_mail):
        self.assertTrue(self._mailer.send_repeat_offender_suspension('test-ticket-id', 'domain', 'test-domain-id',
                                                                     ['test-id'], 'test-url'))

    def test_send_repeat_offender_suspension_no_shoppers(self):
        self.assertFalse(self._mailer.send_repeat_offender_suspension('test-ticket-id', 'domain', 'test-domain-id',
                                                                      [], 'test-url'))

    @patch('hermes.messenger.send_mail', side_efect=OCMException())
    @patch('zeus.events.email.registered_mailer.generate_event', return_value=None)
    def test_send_repeat_offender_suspension_exception(self, generate_event, send_mail):
        self.assertFalse(self._mailer.send_repeat_offender_suspension('test-ticket-id', 'domain', 'test-domain-id',
                                                                      ['test-id'], 'test-url'))
