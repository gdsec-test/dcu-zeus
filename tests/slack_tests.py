import requests
from mock import patch, MagicMock
from nose.tools import assert_true, assert_false

from settings import TestingConfig
from zeus.utils.slack import SlackUtil


class TestSlackUtil:
    @classmethod
    def setup(cls):
        cls._slack_util = SlackUtil(TestingConfig.SLACK_URL, TestingConfig.SLACK_CHANNEL)

    @patch.object(requests, 'post')
    def test_write_to_slack(self, post):
        post.return_value = MagicMock(status_code=200)
        actual = self._slack_util.send_message("hello world")
        assert_true(actual)

    @patch.object(requests, 'post')
    def test_write_to_slack_fail(self, post):
        post.return_value = MagicMock(status_code=404, headers="Test Headers")
        actual = self._slack_util.send_message("hello world")
        assert_false(actual)
