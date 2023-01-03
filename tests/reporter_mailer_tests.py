from unittest import TestCase

from hermes.exceptions import OCMException
from mock import patch

from settings import UnitTestConfig
from zeus.events.email.reporter_mailer import ReporterMailer
from zeus.persist.notification_timeouts import Throttle


class TestReporterMailer(TestCase):
    REPORTER_EMAIL = 'dcuinternal@godaddy.com'
    SOURCE = 'https://example.com'

    def setUp(self):
        self._mailer = ReporterMailer(UnitTestConfig)

    @patch('zeus.events.email.reporter_mailer.send_mail', return_value={})
    @patch('zeus.events.email.reporter_mailer.generate_event')
    @patch.object(Throttle, 'can_reporter_acknowledge_email_be_sent', return_value=True)
    def test_send_hosting_provider_notice_success(self, throttle, gen_event, send_mail):
        self.assertTrue(self._mailer.send_acknowledgement_email(self.SOURCE, self.REPORTER_EMAIL))
        self.assertTrue(throttle.called)
        self.assertTrue(send_mail.called)
        self.assertTrue(gen_event.called)

    @patch('zeus.events.email.reporter_mailer.send_mail', return_value={})
    @patch('zeus.events.email.reporter_mailer.generate_event')
    @patch.object(Throttle, 'can_reporter_acknowledge_email_be_sent', return_value=False)
    def test_send_hosting_provider_notice_fail_throttle(self, throttle, gen_event, send_mail):
        self.assertFalse(self._mailer.send_acknowledgement_email(self.SOURCE, self.REPORTER_EMAIL))
        self.assertTrue(throttle.called)
        self.assertTrue(not send_mail.called)
        self.assertTrue(not gen_event.called)

    @patch('zeus.events.email.reporter_mailer.send_mail', side_effect=OCMException())
    @patch('zeus.events.email.reporter_mailer.generate_event')
    @patch.object(Throttle, 'can_reporter_acknowledge_email_be_sent', return_value=True)
    def test_send_hosting_provider_notice_fail_ocm_exception(self, throttle, gen_event, send_mail):
        self.assertFalse(self._mailer.send_acknowledgement_email(self.SOURCE, self.REPORTER_EMAIL))
        self.assertTrue(throttle.called)
        self.assertTrue(send_mail.called)
        self.assertTrue(gen_event.called)
