import json
import logging
from enum import Enum

import requests


class EventTypes(Enum):
    customer_warning = 'CUSTOMER_WARNING'
    product_suspension = 'PRODUCT_SUSPENSION'
    product_reinstatement = 'PRODUCT_REINSTATEMENT'
    product_cancellation = 'PRODUCT_CANCELLATION'
    content_block = 'CONTENT_BLOCK'
    content_unblock = 'CONTENT_UNBLOCK'
    content_delete = 'CONTENT_DELETE'


class EventReasons(Enum):
    phishing = 'PHISHING'
    malware = 'MALWARE'
    spam = 'SPAM'
    network_abuse = 'NETWORK_ABUSE'
    resolved_by_customer = 'RESOLVED_BY_CUSTOMER'


class Journal:
    _types = {item.value for item in EventTypes}  # Construct mappings of the values for easy set look-up
    _reasons = {item.value for item in EventReasons}

    _headers = {'Accept': 'application/json'}

    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self._sso_endpoint = app_settings.SSO_URL + '/v1/secure/api/token'
        self._journal_endpoint = app_settings.JOURNAL_URL + '/v1/requests'

        cert = (app_settings.ZEUS_SSL_CERT, app_settings.ZEUS_SSL_KEY)
        self._headers.update({'Authorization': self._get_jwt(cert)})

    def write(self, type, product_family, domain, reason, notes, assets=None):
        """
        Create an abuse event entry in DCU Journal to be consumed by Hosting Product Teams, et. al
        :param type: ENUM value associated with EventTypes
        :param product_family: The product family e.g. Domain, GoCentral, Diablo, etc.
        :param domain: The domain this report is for
        :param reason: The type of report this is e.g. PHISHING, MALWARE, etc.
        :param notes: Human readable notes associated with this report, similar to CRM/Netvio notes.
        :param assets: Any associated assets such as URLs
        :return:
        """

        # Check if we received the str representation or the ENUM representation of these fields and convert as needed
        if not isinstance(type, basestring):
            type = type.value
        if not isinstance(reason, basestring):
            reason = reason.value

        if type not in self._types or reason not in self._reasons:
            self._logger.warning("Unable to write to journal. Unsupported type {} or reason {}".format(type, reason))
            return False

        body = {'type': type, 'productFamily': product_family, 'domain': domain, 'reason': reason, 'notes': notes}
        if assets:  # assets are optionally per the model but we will likely always provide them
            body.update({'assets': assets})

        try:
            response = requests.post(self._journal_endpoint, json=body, headers=self._headers)
            response.raise_for_status()
        except Exception as e:
            self._logger.error(e.message)

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
