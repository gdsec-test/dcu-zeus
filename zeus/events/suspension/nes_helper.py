import logging
import json
import string
import requests
from settings import AppConfig

class NESHelper():
    _headers = {'Content-Type': 'application/json'}
    SUSPEND_REASON = "POLICY"  # POLICY - means it's being suspended for ABUSE

    SUSPEND_CMD = 'suspendByEntitlementId'
    REINSTATE_CMD = 'reinstateByEntitlementId'

    VALID_ENTITLEMENT_STATUS = ['ACTIVE', 'SUSPENDED', 'PEND_CANCEL', 'CANCELLED']
    ENTITLEMENT_ERROR_MSG = 'Get entitlement returned error.  Status code: {}; Message: {}'
    SUSPENSION_ERROR_MSG = 'Subsriptions API {} returned error.  Status code: {}; Message: {}'

    def __init__(self, settings: AppConfig):
        self._logger = logging.getLogger(__name__)
        self._subscriptions_url = settings.NES_URL
        self._entitlement_url = settings.ENTITLEMENT_URL
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
            url = self._subscriptions_url.format(customer_id, url_cmd)
            body = {'entitlementId': entitlement_id, 'suspendReason': self.SUSPEND_REASON}
            response = requests.post(url, json=body, headers=self._headers, verify=True)

            # If these credentials aren't accepted, update the JWT and try again
            if response.status_code in [401, 403]:
                self._headers.update({'Authorization': f'sso-jwt {self._get_jwt(self._cert)}'})
                response = requests.post(url, json=body, headers=self._headers, verify=True)

            # process response and log errors and successes
            if response.status_code != 204:
                self._logger.error(f'Failed to suspend customerId: {customer_id}; entitlementId: {entitlement_id}.\nResponse was: Status code = {response.status_code}\nMessage ={response.text}')
                return self.SUSPENSION_ERROR_MSG.format(url_cmd, response.status_code, response.text)
            else:
                self._logger.info(f'Successfully requested suspension for customerId: {customer_id}; entitlementId: {entitlement_id}')
            
            # Now, we need to poll for the entitlement status to be correct
            expected_stauts = 'SUSPEND' if url_cmd == self._SUSPEND_CMD else 'ACTIVE'
            return self._poll_for_entitlement_status(entitlement_id, customer_id, expected_stauts)
        except Exception as e:
            self._logger.error(f'Failed to suspend customerId: {customer_id}; entitlementId: {entitlement_id} with exception: {e}')
            return False

    def _poll_for_entitlement_status(self, entitlement_id, customer_id, status):
        # TODO: add some sort of timeout!!!
        while(1):
            status_resposne = self._check_entitlement_status(customer_id, entitlement_id)
            # If the response from 'check entitlement status' is not one of the valid status codes, then we know an error happened.  Return that error
            if status_resposne not in self.VALID_ENTITLEMENT_STATUS:
                return status_resposne
            # If the resposne is the status we are looking for, return true
            if status_resposne == status:
                # TODO: log success message
                return True


    def _check_entitlement_status(self, entitlement_id, customer_id):
        url = self._entitlement_url.format(customer_id, entitlement_id)
        response = requests.get(url, headers=self._headers, verify=True)

        # If the credentials aren't accepted, update the JWT and try again
        if response.status_code in [401, 403]:
            self._headers.update({'Authorization': f'sso-jwt {self._get_jwt(self._cert)}'})
            response = requests.get(url, headers=self._headers, verify=True)
        
        # If the response is 200, parse the response for the desired status
        # If the response is anything else, return an error note to the user
        if response.status_code == 200:
            resp_dict = json.loads(response.text)
            entitlement_status = resp_dict.get('status')
            self._logger.info(f'Successfully got entitlement data for for customerId: {customer_id}; entitlementId: {entitlement_id}.  Status was: {entitlement_status}')
            return entitlement_status

        self._logger.error(f'Failed to get entitlement data for customerId: {customer_id}; entitlementId: {entitlement_id}.\nResponse was: Status code = {response.status_code}\nMessage = {response.text}')
        return self.ENTITLEMENT_ERROR_MSG.format(response.status_code, response.text)


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