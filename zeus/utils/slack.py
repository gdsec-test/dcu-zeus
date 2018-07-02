import json
import requests
import logging

from zeus.persist.persist import Persist


class SlackUtil(object):
    SLACK_USERNAME = 'Zeus'

    def __init__(self, url, channel):
        self._logger = logging.getLogger(__name__)
        self._url = url
        self._channel = channel

    def send_message(self, message):
        if not message:
            return False

        try:
            payload = {'payload': json.dumps({
                'channel': self._channel,
                'username': self.SLACK_USERNAME,
                'text': message})
            }
            response = requests.post(self._url, data=payload)

            # Check for HTTP response codes from SNOW for other than 200
            if response.status_code != 200:
                self._logger.warning("Status: {} Headers: {} Error: {}".format(response.status_code,
                                                                               response.headers,
                                                                               response.json()))
        except Exception as e:
            self._logger.warning("Error posting message to slack {}".format(e.message))


class ThrottledSlack(object):
    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self._decorated = SlackUtil(app_settings.SLACK_URL, app_settings.SLACK_CHANNEL)
        self._throttle = Persist(app_settings.REDIS, app_settings.NOTIFICATION_LOCK_TIME)

    def send_message(self, key, message):
        if self._throttle.can_slack_message_be_sent(key):
            self._decorated.send_message(message)


class SlackFailures:
    def __init__(self, slack):
        self._logger = logging.getLogger(__name__)
        self._slack = slack

    def failed_netvio_creation(self, guid):
        key = '{}_create_netvio_failed'.format(guid)
        message = 'Unable to create NetVio ticket for {}'.format(guid)
        self._logger.warning(message)
        self._slack.send_message(key, message)

    def failed_hosting_suspension(self, guid):
        key = '{}_suspend_failed'.format(guid)
        message = 'Suspension Failed for Hosting: {}'.format(guid)
        self._logger.warning(message)
        self._slack.send_message(key, message)

    def failed_domain_suspension(self, domain):
        key = '{}_suspend_failed'.format(domain)
        message = 'Suspension Failed for Domain: {}'.format(domain)
        self._logger.warning(message)
        self._slack.send_message(key, message)

    def invalid_abuse_type(self, ticket_id):
        key = '{}_not_valid_hold'.format(ticket_id)
        message = '{} not placed on hold - not a valid ticket type'.format(ticket_id)
        self._logger.warning(message)
        self._slack.send_message(key, message)

    def invalid_hosted_status(self, ticket_id):
        key = '{}_not_valid_hold'.format(ticket_id)
        message = '{} not placed on hold - not a valid hosted status'.format(ticket_id)
        self._logger.warning(message)
        self._slack.send_message(key, message)

    def failed_to_determine_shoppers(self, ticket_id):
        key = '{}_suspend_failed_no_shopper'.format(ticket_id)
        message = 'No action taken for {} - unable to determine shopper'.format(ticket_id)
        self._logger.warning(message)
        self._slack.send_message(key, message)

    def failed_to_determine_guid(self, ticket_id):
        key = '{}_suspend_failed_no_guid'.format(ticket_id)
        message = 'No action taken for {} - no GUID could be found'.format(ticket_id)
        self._logger.warning(message)
        self._slack.send_message(key, message)

    def failed_sending_email(self, ticket_id):
        key = '{}_email_failed_to_send'.format(ticket_id)
        message = 'Email failed to send for {}'.format(ticket_id)
        self._logger.warning(message)
        self._slack.send_message(key, message)
