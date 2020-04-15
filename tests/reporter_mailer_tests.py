from hermes.exceptions import OCMException
from mock import patch
from nose.tools import assert_false, assert_true

from settings import TestingConfig
from zeus.events.email.reporter_mailer import ReporterMailer


class TestForeignMailer(object):

    @classmethod
    def setup(cls):
        cls._mailer = ReporterMailer(TestingConfig)

    @patch('zeus.events.email.reporter_mailer.send_mail', return_value={})
    @patch('zeus.events.email.reporter_mailer.generate_event')
    def test_send_hosting_provider_notice(self, mock_event, send_mail):
        assert_true(self._mailer.send_acknowledgement_email('ticket_id', 'dcuinternal@godaddy.com'))

    @patch('zeus.events.email.reporter_mailer.send_mail', side_effect=OCMException())
    @patch('zeus.events.email.reporter_mailer.generate_event')
    def test_send_hosting_provider_notice_ocm_exception(self, mock_event, send_mail):
        assert_false(self._mailer.send_acknowledgement_email('ticket_id', 'dcuinternal@godaddy.com'))
