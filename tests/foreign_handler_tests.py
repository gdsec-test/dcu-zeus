from mock import patch
from nose.tools import assert_false, assert_true

from settings import TestingConfig
from zeus.events.email.foreign_mailer import ForeignMailer
from zeus.handlers.foreign_handler import ForeignHandler
from zeus.reviews.reviews import BasicReview
from zeus.utils.slack import SlackFailures


class TestForeignHandler:
    ticket_invalid_type = {'hosted_status': 'FOREIGN'}
    ticket_valid = {'hosted_status': 'FOREIGN', 'type': 'PHISHING'}

    @classmethod
    def setup(cls):
        cls._foreign = ForeignHandler(TestingConfig)

    @patch.object(SlackFailures, 'invalid_hosted_status', return_value=None)
    def test_foreign_notice_unsupported_hosted_status(self, slack):
        assert_false(self._foreign.foreign_notice({}))

    @patch.object(SlackFailures, 'invalid_abuse_type', return_value=None)
    def test_foreign_notice_unsupported_type(self, slack):
        assert_false(self._foreign.foreign_notice(self.ticket_invalid_type))

    @patch.object(ForeignMailer, 'send_foreign_hosting_notice', return_value=False)
    @patch.object(BasicReview, 'place_in_review', return_value=None)
    @patch.object(SlackFailures, 'failed_to_send_foreign_hosting_notice', return_value=None)
    def test_foreign_notice_failure(self, slack, review, mail):
        assert_false(self._foreign.foreign_notice(self.ticket_valid))

    @patch.object(ForeignMailer, 'send_foreign_hosting_notice', return_value=True)
    @patch.object(BasicReview, 'place_in_review', return_value=None)
    def test_foreign_notice(self, review, mail):
        assert_true(self._foreign.foreign_notice(self.ticket_valid))
