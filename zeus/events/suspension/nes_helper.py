import logging
import json
import requests
from settings import AppConfig


class NESHelper():
    _headers = {'Content-Type': 'application/json'}
    SUSPEND_REASON = "POLICY"  # POLICY - means it's being suspended for ABUSE

    SUSPEND_CMD = 'suspendByEntitlementId'
    REINSTATE_CMD = 'reinstateByEntitlementId'

    VALID_ENTITLEMENT_STATUSES = ['ACTIVE', 'SUSPENDED', 'PEND_CANCEL', 'CANCELLED']
    ENTITLEMENT_ERROR_MSG = 'Get entitlement returned error.  Status code: {}; Message: {}'
    SUSPENSION_ERROR_MSG = 'Subsriptions API {} returned error.  Status code: {}; Message: {}'

    def __init__(self, settings: AppConfig):
        self._logger = logging.getLogger(__name__)
        # Note: the first variable is the customerID and the second one is the suspend / reinstate command  (i.e. "suspendByEntitlementId")
        self._nes_url = settings.SUBSCRIPTIONS_URL.format(f'customers/{}/{}')
        self._health_check_url = settings.SUBSCRIPTIONS_URL.format('subscriptions-shim/healthcheck')
        self._entitlement_url = settings.ENTITLEMENT_URL
        self._sso_endpoint = settings.SSO_URL

        # TODO LKM: make sure these endpoints have the zeus cert whitelisted - requested in
        #  https://godaddy-corp.atlassian.net/browse/EP-49428 and
        #  https://godaddy-corp.atlassian.net/browse/EP-49484
        self._cert = (settings.ZEUS_CLIENT_CERT, settings.ZEUS_CLIENT_KEY)
        self._headers.update({'Authorization': f'sso-jwt {self._get_jwt(self._cert)}'})

    def suspend(self, entitlement_id, customer_id):
        return self._perform_request(entitlement_id, customer_id, self.SUSPEND_CMD)

    def reinstate(self, entitlement_id, customer_id):
        return self._perform_request(entitlement_id, customer_id, self.REINSTATE_CMD)

    def run_healthcheck(self):
        response = requests.post(self._health_check_url, headers=self._headers, verify=True)
        # TODO LKM: parse response!
        return True

    def _perform_request(self, entitlement_id, customer_id, url_cmd):
        try:
            url = self._nes_url.format(customer_id, url_cmd)
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
        # TODO LKM: add some sort of timeout!!!  Need to first figure out how long it usually takes
        while(1):
            status_resposne = self._check_entitlement_status(customer_id, entitlement_id)
            # If the response from 'check entitlement status' is not one of the valid statuses, then we know an error happened.  Return that error
            if status_resposne not in self.VALID_ENTITLEMENT_STATUSES:
                return status_resposne
            # If the resposne is the status we are looking for, return true
            if status_resposne == status:
                self._logger.info(f'Entitlement {entitlement_id} succesfully changed to status {status_resposne}')
                return True

    def _check_entitlement_status(self, entitlement_id, customer_id):
        url = self._entitlement_url.format(customer_id, entitlement_id)
        response = requests.get(url, headers=self._headers, verify=True)

        # If the credentials aren't accepted, update the JWT and try again
        if response.status_code in [401, 403]:
            self._headers.update({'Authorization': f'sso-jwt {self._get_jwt(self._cert)}'})
            response = requests.get(url, headers=self._headers, verify=True)

        # If the response is 200, parse the response for the desired status
        if response.status_code == 200:
            resp_dict = json.loads(response.text)
            entitlement_status = resp_dict.get('status')
            self._logger.info(f'Successfully got entitlement data for for customerId: {customer_id}; entitlementId: {entitlement_id}.  Status was: {entitlement_status}')
            return entitlement_status

        # If the response is anything else, log the error, and return an error note to the user
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
