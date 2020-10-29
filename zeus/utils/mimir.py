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
    suspended_csam = 'SUSPENDED_CSAM'


class Mimir:
    _headers = {'Accept': 'application/json'}

    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self._sso_endpoint = app_settings.SSO_URL + '/v1/secure/api/token'
        self._mimir_endpoint = app_settings.MIMIR_URL + '/v1/infractions'
        self.slack = SlackFailures(ThrottledSlack(app_settings))
        cert = (app_settings.ZEUS_SSL_CERT, app_settings.ZEUS_SSL_KEY)
        self._headers.update({'Authorization': self._get_jwt(cert)})

    @staticmethod
    def _clean_dict_for_mimir(query_dict):
        """
        Remove any keys which have an empty or None value
        :param query_dict: dictionary of Mimir query parameters
        """
        return {k: v for k, v in query_dict.items() if v}

    def write(self,
              abuse_type,
              domain,
              hosted_status,
              infraction_type,
              shopper_number,
              ticket_number,
              domain_id=None,
              guid=None,
              ncmec_report_id=None,
              note=None):
        """
        Create an infraction entry in DCU Mimir
        :param abuse_type: Abuse Type of the incident
        :param domain: Domain name
        :param hosted_status: HOSTED, REGISTERED or FOREIGN
        :param infraction_type: One of CONTENT_REMOVED, CUSTOMER_WARNING, EXTENSIVE_COMPROMISE, INTENTIONALLY_MALICIOUS,
            REPEAT_OFFENDER, SHOPPER_COMPROMISE or SUSPENDED
        :param shopper_number: Shopper account number
        :param ticket_number: DCU SNOW ticket number
        :param domain_id: Optional: The domain identifier
        :param guid: Optional: Guid of hosting account
        :param ncmec_report_id: Optional: NCMEC Report ID from NCMEC report submissions for CSAM infractions
        :param note: Optional: Mimir note in case of CSAM infractions
        :return:
        """

        # Check if we received the str representation or the ENUM representation of these fields and convert as needed
        if not isinstance(infraction_type, basestring):
            infraction_type = infraction_type.value

        body = {'abuseType': abuse_type,
                'domainId': domain_id,
                'hostedStatus': hosted_status,
                'hostingGuid': guid,
                'infractionType': infraction_type,
                'ncmecReportID': ncmec_report_id,
                'note': note,
                'shopperId': shopper_number,
                'sourceDomainOrIp': domain,
                'ticketId': ticket_number
                }
        body = Mimir._clean_dict_for_mimir(body)

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
