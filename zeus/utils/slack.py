import json
import requests
import logging

from zeus.persist.persist import Persist


class SlackUtil(object):
    SLACK_USERNAME = 'Zeus'
    _logger = logging.getLogger(__name__)

    def __init__(self, url, channel):
        self._url = url
        self._channel = channel

    def send_message(self, message):
        if not message:
            return False

        payload = {'payload': json.dumps({
            'channel': self._channel,
            'username': self.SLACK_USERNAME,
            'text': message})
        }
        response = requests.post(self._url, data=payload)

        # Check for HTTP response codes from SNOW for other than 200
        if response.status_code != 200:
            self._logger.warning('Status: {} Headers: {} Error: {}'.format(response.status_code,
                                                                           response.headers,
                                                                           response.json()))
            return False
        return True


class ThrottledSlack(object):
    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self._decorated = SlackUtil(app_settings.SLACK_URL, app_settings.SLACK_CHANNEL)
        self._throttle = Persist(app_settings.REDIS, app_settings.NOTIFICATION_LOCK_TIME)

    def send_message(self, key, message):
        if self._throttle.can_slack_message_be_sent(key):
            self._decorated.send_message(message)
