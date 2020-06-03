import json
import logging
from enum import Enum

import requests

from zeus.utils.slack import SlackFailures, ThrottledSlack


class InfractionTypes(Enum):
    customer_warning = 'CUSTOMER_WARNING'
    content_removed = 'CONTENT_REMOVED'
    intentionally_malicious = 'INTENTIONALLY_MALICIOUS'
    repeat_offender = 'REPEAT_OFFENDER'
    shopper_compromise = 'SHOPPER_COMPROMISE'
    suspended = 'SUSPENDED'
    extensive_compromise = 'EXTENSIVE_COMPROMISE'
    ncmec_report_submitted = 'NCMEC_REPORT_SUBMITTED'


class Mimir:
    _types = {item.value for item in InfractionTypes}  # Construct mappings of the values for easy set look-up
    _headers = {'Accept': 'application/json'}

    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self._sso_endpoint = app_settings.SSO_URL + '/v1/secure/api/token'
        self._mimir_endpoint = app_settings.MIMIR_URL + '/v1/infractions'
        self.slack = SlackFailures(ThrottledSlack(app_settings))
        cert = (app_settings.ZEUS_SSL_CERT, app_settings.ZEUS_SSL_KEY)
        self._headers.update({'Authorization': self._get_jwt(cert)})

    def write(self, infraction_type, shopper_number, ticket_number, domain, guid, note=None, ncmecReportID=None):
        """
        Create an infraction entry in DCU Mimir
        :param infraction_type: One of CONTENT_REMOVED, CUSTOMER_WARNING, EXTENSIVE_COMPROMISE, INTENTIONALLY_MALICIOUS,
            REPEAT_OFFENDER, SHOPPER_COMPROMISE or SUSPENDED
        :param shopper_number: Shopper account number
        :param ticket_number: DCU SNOW ticket number
        :param domain: Domain name
        :param guid: Guid of hosting account
        :param note: Mimir note in case of CSAM infractions
        :param ncmecReportID: NCMEC Report ID from NCMEC report submissions for CSAM infractions
        :return:
        """

        # Check if we received the str representation or the ENUM representation of these fields and convert as needed
        if not isinstance(infraction_type, basestring):
            infraction_type = infraction_type.value

        if infraction_type not in self._types:
            message = 'Unable to write to mimir. Unsupported type {}'.format(type)
            self.slack.failed_infraction_creation(guid, ticket_number, message)
            return

        body = {'infractionType': infraction_type, 'shopperId': shopper_number, 'ticketId': ticket_number,
                'sourceDomainOrIp': domain, 'hostingGuid': guid, 'note': note, 'ncmecReportID': ncmecReportID}

        try:
            response = requests.post(self._mimir_endpoint, json=body, headers=self._headers)

            if response.status_code not in {200, 201}:
                self.slack.failed_infraction_creation(guid, ticket_number, response.reason)

        except Exception as e:
            self.slack.failed_infraction_creation(guid, ticket_number, e.message)

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
