import requests
from mock import MagicMock, patch
from nose.tools import assert_equal

from settings import TestingConfig
from zeus.utils.crmalert import CRMAlert
from zeus.utils.slack import SlackFailures


class TestCRMAlert:
    @classmethod
    def setup_class(cls):
        cls._crmalert = CRMAlert(TestingConfig())

    @patch.object(requests, 'post')
    def test_create_alert_success(self, requests_mocked_method):
        requests_mocked_method.return_value = MagicMock(status_code=201)
        requests_mocked_method.return_value.json.return_value = {'_id': "12ab34cd"}
        assert_equal(self._crmalert.create_alert("1234", "Message", "PHISHING", "LOW", "zeus.com", "Resolution"), "12ab34cd")

    @patch.object(requests, 'post')
    @patch.object(SlackFailures, 'failed_to_create_alert', return_value=None)
    def test_create_alert_fail(self, requests_mocked_method, slack_mocked_method):
        requests_mocked_method.return_value = MagicMock(status_code=400)
        requests_mocked_method.return_value.json.return_value = None
        assert_equal(self._crmalert.create_alert("1234", "Message", "PHISHING", "LOW", "zeus.com", "Resolution"), None)

    @patch.object(requests, 'post', return_value=None)
    @patch.object(SlackFailures, 'failed_to_create_alert', return_value=None)
    def test_create_alert_exception(self, requests_mocked_method, slack_mocked_method):
        assert_equal(self._crmalert.create_alert("1234", "Message", "PHISHING", "LOW", "zeus.com", "Resolution"), None)
