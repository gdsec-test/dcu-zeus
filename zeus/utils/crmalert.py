import json
import logging

import requests

from zeus.utils.slack import SlackFailures, ThrottledSlack


class CRMAlert:
    _headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    low_severity = "LOW"
    high_severity = "HIGH"
    initiator = "DCU Zeus Automation"
    _resolution = "http://x.co/dcuwhat2do"

    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self._crmalert_url = app_settings.CRMALERT_URL
        self._sso_endpoint = app_settings.SSO_URL + '/v1/secure/api/token'

        self.slack = SlackFailures(ThrottledSlack(app_settings))

        cert = (app_settings.ZEUS_SSL_CERT, app_settings.ZEUS_SSL_KEY)
        self._headers.update({'Authorization': 'sso-jwt {}'.format(self._get_jwt(cert))})

    def create_alert(self, shopper_id, message, abuse_type, severity, source, resolution=_resolution):
        """
        Create CRM alert for the given arguments. API: https://github.secureserver.net/digital-crimes/crm-alert
        Sends a slack message if CRM alert creation fails

        :param shopper_id: Shopper account ID
        :param message: message to be added to CRM alert stating the reason for creating the alert
        :param abuse_type: Abuse types to be one amongst PHISHING, MALWARE, NETWORK_ABUSE, SPAM, CHILD_ABUSE, FRAUD_WIRE, CONTENT
        :param severity: Severity to be one amongst LOW, HIGH
        :param source: domain where the content resides
        :param resolution: Resolution steps for this account
        :return:
        """

        endpoint = self._crmalert_url + '/v1/alerts'
        body = {'shopperId': shopper_id, 'initiator': self.initiator, 'message': message, 'abuseType': abuse_type,
                'severity': severity, 'source': source, 'resolution': resolution}

        try:
            response = requests.post(endpoint, json=body, headers=self._headers)

            if response.status_code in [200, 201]:
                self._logger.info('Successfully created CRM alert for ShopperID {} Source {} with UUID: {}'.format(
                    shopper_id, source, response.json().get('_id')))
                return response.json().get('_id')

            self._logger.error('Failed to create CRM alert for ShopperID {} Source {} with error {}'.format(
                shopper_id, source, response.reason))
        except Exception as e:
            self._logger.error('Failed to create CRM alert for ShopperID {} Source {} with exception: {}'.format(shopper_id, source, e.message))
        self.slack.failed_to_create_alert(source, shopper_id)
        return None

    def _get_jwt(self, cert):
        """
        Attempt to retrieve the JWT associated with the cert/key pair from SSO
        :param cert:
        :return:
        """
        try:
            response = requests.post(self._sso_endpoint, data={'realm': 'cert'}, cert=cert)
            response.raise_for_status()

            body = json.loads(response.text)
            return body.get('data')  # {'type': 'signed-jwt', 'id': 'XXX', 'code': 1, 'message': 'Success', 'data': JWT}
        except Exception as e:
            self._logger.error(e.message)
        return None
