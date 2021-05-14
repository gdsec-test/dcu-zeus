import json
import logging

import requests

from zeus.persist.notification_timeouts import Throttle


class SlackUtil(object):
    SLACK_USERNAME = 'Zeus'

    def __init__(self, url, channel):
        self._logger = logging.getLogger('celery.tasks')
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
                self._logger.error("Status: {} Headers: {} Error: {}".format(response.status_code,
                                                                             response.headers,
                                                                             response.json()))
        except Exception as e:
            self._logger.error(f'Error posting message to slack {e}')


class ThrottledSlack(object):
    def __init__(self, app_settings):
        self._logger = logging.getLogger('celery.tasks')
        self._decorated = SlackUtil(app_settings.SLACK_URL, app_settings.SLACK_CHANNEL)
        self._throttle = Throttle(app_settings.REDIS, app_settings.NOTIFICATION_LOCK_TIME)

    def send_message(self, key, message):
        if self._throttle.can_slack_message_be_sent(key):
            self._decorated.send_message(message)


class SlackFailures:
    def __init__(self, slack):
        self._logger = logging.getLogger('celery.tasks')
        self._slack = slack

    def failed_hosting_suspension(self, guid, info=''):
        key = f'{guid}_suspend_failed'
        message = f'Suspension Failed for Hosting: {guid}. {info}'
        self._logger.error(message)
        self._slack.send_message(key, message)

    def failed_domain_suspension(self, domain):
        key = f'{domain}_suspend_failed'
        message = f'Suspension Failed for Domain: {domain}'
        self._logger.error(message)
        self._slack.send_message(key, message)

    def failed_protected_domain_action(self, domain, action):
        key = f'{domain}_{action}_action_failed'
        message = f'{action} Action failed for a Protected Domain: {domain}'
        self._logger.error(message)
        self._slack.send_message(key, message)

    def invalid_abuse_type(self, ticket_id):
        key = f'{ticket_id}_not_valid_hold'
        message = f'{ticket_id} not placed on hold - not a valid ticket type'
        self._logger.error(message)
        self._slack.send_message(key, message)

    def invalid_hosted_status(self, ticket_id):
        key = f'{ticket_id}_no action taken'
        message = f'{ticket_id} no action taken - not a valid hosted status'
        self._logger.error(message)
        self._slack.send_message(key, message)

    def failed_to_determine_shoppers(self, ticket_id):
        key = f'{ticket_id}_suspend_failed_no_shopper'
        message = f'No action taken for {ticket_id} - unable to determine shopper'
        self._logger.error(message)
        self._slack.send_message(key, message)

    def failed_to_send_foreign_hosting_notice(self, domain):
        key = f'{domain}_failed_foreign_notice'
        message = f'No foreign notice sent for {domain}'
        self._logger.error(message)
        self._slack.send_message(key, message)

    def failed_to_determine_guid(self, ticket_id):
        key = f'{ticket_id}_suspend_failed_no_guid'
        message = f'No action taken for {ticket_id} - no GUID could be found'
        self._logger.error(message)
        self._slack.send_message(key, message)

    # Identifier will be ticketId in case of CHILD_ABUSE tickets,
    # domain for other abuse types.
    def failed_sending_email(self, identifier):
        key = f'{identifier}_email_failed_to_send'
        message = f'Email failed to send for {identifier}'
        self._logger.error(message)
        self._slack.send_message(key, message)

    def failed_infraction_creation(self, guid, ticket_number, exception_message):
        key = f'{guid}/{ticket_number}_create_infraction_failed'
        message = f'Unable to create Mimir infraction for {guid}/{ticket_number}: {exception_message}'
        self._slack.send_message(key, message)

    def failed_to_create_alert(self, domain, shopper_id):
        key = f'{domain}_failed_to_create_alert'
        message = f'Failed to create alert for domain: {domain} shopperId: {shopper_id}'
        self._slack.send_message(key, message)

    def failed_sending_revocation_email(self, ticket_id, domain, shopper_id, ssl_subscription):
        key = f'{domain}_ssl_email_failed_to_send'
        message = f'SSL revocation email failed to send for ticketId: {ticket_id}' \
                  f' shopperId: {shopper_id} domain: {domain} ssl: {ssl_subscription}'
        self._logger.error(message)
        self._slack.send_message(key, message)
