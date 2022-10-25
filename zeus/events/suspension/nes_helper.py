import logging
import json
import requests
from settings import AppConfig

class NESHelper():
    _headers = {'Content-Type': 'application/json'}
    SUSPEND_REASON = "POLICY"  # POLICY - means it's being suspended for ABUSE

    SUSPEND_CMD = 'suspendByEntitlementId'
    REINSTATE_CMD = 'reinstateByEntitlementId'

    def __init__(self, settings: AppConfig):
        self._logger = logging.getLogger(__name__)
        self._url = settings.NES_URL
        self._sso_endpoint = settings.SSO_URL
        
        # TODO: LKM - make sure this endpoint has the zeus cert whitelisted
        self._cert = (settings.ZEUS_CLIENT_CERT, settings.ZEUS_CLIENT_KEY)
        self._headers.update({'Authorization': f'sso-jwt {self._get_jwt(self._cert)}'})

    def suspend(self, entitlement_id, customer_id):
        return self._perform_request(entitlement_id, customer_id, self.SUSPEND_CMD)
    
    def reinstate(self, entitlement_id, customer_id):
        return self._perform_request(entitlement_id, customer_id, self.REINSTATE_CMD)

    def _perform_request(self, entitlement_id, customer_id, url_cmd):
        try:
            url = self._url.format(customer_id, url_cmd)
            body = {'entitlementId': entitlement_id, 'suspendReason': self.SUSPEND_REASON}
            response = requests.post(url, json=body, headers=self._headers, verify=True)

            # If these credentials aren't accepted, update the JWT and try again
            if response.status_code in [401, 403]:
                self._headers.update({'Authorization': f'sso-jwt {self._get_jwt(self._cert)}'})
                response = requests.post(url, json=body, headers=self._headers, verify=True)

            # TODO: LKM - process response and log errors and successes; return corresponding results, NOT just true / false
            if response.status_code != 204:
                resp_message = response.json().get('message', {})
                self._logger.error(f'Failed to suspend customerId: {customer_id}; entitlementId: {entitlement_id}.\nResponse was: Status code = {response.status_code}\nMessage ={resp_message}')
            else:
                # TODO: LKM - will want to log an event for this
                self._logger.info(f'Successfully suspended customerId: {customer_id}; entitlementId: {entitlement_id}')
            return response.status_code == 204

            # TODO: ALSO verify reinstatement is done?  OR should we do that in a different function?
        except Exception as e:
            self._logger.error(f'Failed to suspend customerId: {customer_id}; entitlementId: {entitlement_id} with exception: {e}')
            return False


    def _get_jwt(self, cert):
        """
        Attempt to retrieve the JWT associated with the cert/key pair from SSO
        :param cert: tuple of cert, key
        :return: JWT string or None
        """
        try:
            response = requests.post(self._sso_endpoint, data={'realm': 'cert'}, cert=cert)
            response.raise_for_status()

            body = json.loads(response.text)
            return body.get('data')  # {'type': 'signed-jwt', 'id': 'XXX', 'code': 1, 'message': 'Success', 'data': JWT}
        except Exception as e:
            self._logger.error(e)