import logging
import json
import requests
import time
import os
from settings import AppConfig
from redis import Redis
from datetime import timedelta
from zeus.utils.functions import get_host_info_from_dict


class ThrottledNESHelper():
    def __init__(self, app_settings):
        self._decorated = NESHelper(app_settings)

    def get_nes_state(self):
        return self._decorated.get_nes_state()

    def get_use_nes(self, data):
        return self._decorated.get_use_nes(data)


class NESHelper():
    _headers = {'Content-Type': 'application/json'}
    SUSPEND_REASON = 'POLICY'  # POLICY - means it's being suspended for ABUSE

    SUSPEND_CMD = 'suspendByEntitlementId'
    REINSTATE_CMD = 'reinstateByEntitlementId'

    VALID_ENTITLEMENT_STATUSES = ['ACTIVE', 'SUSPENDED', 'PEND_CANCEL', 'CANCELLED']
    MESSAGE = "Requested {} on entitlement ID: {}, customer ID: {}.  Status = {}.  Message = {}"

    REDIS_EXPIRATION = timedelta(days=5)
    REDIS_NES_STATE_KEY = 'nes-state'
    REDIS_NES_STATE_GOOD = 'UP'
    REDIS_NES_STATE_BAD = 'DOWN'

    # TODO CMAPT-5272: remove the NES selection flags
    PRODUCTS_USE_NES_FLAG = {
        'diablo': os.getenv("DIABLO_USE_NES", False),
        'vertigo': os.getenv("VERTIGO_USE_NES", False),
        'mwp 1.0': os.getenv("MWPONE_USE_NES", False),
        'plesk': os.getenv("ANGELO_USE_NES", False),
        'vps4': os.getenv("VPS4_USE_NES", False),
        'gocentral': os.getenv("GOCENTRAL_USE_NES", False)
    }
    ALL_USE_NES_FLAG = os.getenv("ALL_USE_NES")

    def __init__(self, settings: AppConfig):
        self._logger = logging.getLogger(__name__)

        # Note: the first variable is the customerID and the second one is the suspend / reinstate command  (i.e. "suspendByEntitlementId")
        self._nes_url = settings.SUBSCRIPTIONS_URL.format('v2/customers/{}/{}')
        # Note: first var is the customer ID and the second is the entitlement ID
        self._entitlement_url = settings.ENTITLEMENT_URL.format('v2/customers/{}/entitlements/{}')
        self._sso_endpoint = settings.SSO_URL

        # TODO LKM: make sure these endpoints have the zeus cert whitelisted - this was requested in
        #  https://godaddy-corp.atlassian.net/browse/EP-49428 and
        #  https://godaddy-corp.atlassian.net/browse/EP-49484
        self._cert = (settings.ZEUS_CLIENT_CERT, settings.ZEUS_CLIENT_KEY)
        self._headers.update({'Authorization': f'sso-jwt {self._get_jwt(self._cert)}'})

        # NOTE: if you switch this to StrictRedis, you MUST also update the call to 'setex' below.
        # In the version of redis we are currently using, the 'time' and 'value' parameters for 'setex' were flipped:
        #  value first, then time.  In other version of redis, as well as the StrictRedis the parameters are: time, then value.
        self._redis = Redis(settings.REDIS)

    def suspend(self, entitlement_id, customer_id):
        # If suspension succeeded, poll for entitlement status
        if(self._do_suspend_reinstate(entitlement_id, customer_id, self.SUSPEND_CMD)):
            return self.wait_for_entitlement_status(entitlement_id, customer_id, 'SUSPEND')
        return False

    def reinstate(self, entitlement_id, customer_id):
        # If reinstatement succeeded, poll for entitlement status
        if(self._do_suspend_reinstate(entitlement_id, customer_id, self.REINSTATE_CMD)):
            return self.wait_for_entitlement_status(entitlement_id, customer_id, 'ACTIVE')
        return False

    def get_nes_state(self):
        nes_state = self._redis.get(self.REDIS_NES_STATE_KEY)
        if nes_state:
            state = nes_state.decode()
            return state == self.REDIS_NES_STATE_GOOD
        # If the nes-state isn't set, assume that it is good
        return True

    def set_nes_state(self, state):
        self._redis.setex(self.REDIS_NES_STATE_KEY, state, self.REDIS_EXPIRATION)

    # TODO CMAPT-5272: remove this function and all references to it
    def get_use_nes(self, data):
        # Only check if we should use NES if this is a hosted product
        hosted_status = data.get('hosted_status') or data.get('hostedStatus')
        if hosted_status == 'HOSTED':
            product = get_host_info_from_dict(data).get('product')
            return self.PRODUCTS_USE_NES_FLAG.get(product, 'False') == 'True' or self.ALL_USE_NES_FLAG == 'True'
        return False

    def wait_for_entitlement_status(self, entitlement_id, customer_id, status):
        # TODO LKM: add some sort of timeout!!!  Need to first figure out how long it usually takes
        # TODO LKM: ALSO we want to log how long this takes
        while(1):
            status_resposne = self._check_entitlement_status(customer_id, entitlement_id)
            # If the response from 'check entitlement status' is not one of the valid statuses, then we know an error happened.  Return False
            if status_resposne not in self.VALID_ENTITLEMENT_STATUSES:
                return False
            # If the resposne is the status we are looking for, return true
            if status_resposne == status:
                self._logger.info(f'Entitlement {entitlement_id} succesfully changed to status {status_resposne}')
                return True
            time.sleep(1)

    def _do_suspend_reinstate(self, entitlement_id, customer_id, url_cmd):
        try:
            url = self._nes_url.format(customer_id, url_cmd)
            body = {'entitlementId': entitlement_id, 'suspendReason': self.SUSPEND_REASON}
            response = requests.post(url, json=body, headers=self._headers)

            # If these credentials aren't accepted, update the JWT and try again
            if response.status_code in [401, 403]:
                self._headers.update({'Authorization': f'sso-jwt {self._get_jwt(self._cert)}'})
                response = requests.post(url, json=body, headers=self._headers)

            # LKM TODO: figure out if we also want to set it if we get a 502 bad gateway
            # If we get a 500 error, set the NES state in redis
            if response.status_code == 500:
                self.set_nes_state(self.REDIS_NES_STATE_BAD)
            else:
                self.set_nes_state(self.REDIS_NES_STATE_GOOD)

            # process response and log errors and successes
            if response.status_code != 204:
                error_msg = self.MESSAGE.format(url_cmd, entitlement_id, customer_id, f'POST request returned error {response.status_code}', response.text)
                self._logger.error(error_msg)
                return False
            else:
                self._logger.info(self.MESSAGE.format(url_cmd, entitlement_id, customer_id, 'Success!', 'N/A'))
                return True

        except Exception as e:
            error_msg = self.MESSAGE.format(url_cmd, entitlement_id, customer_id, 'EXCEPTION thrown', e)
            self._logger.exception(error_msg)
            self.set_nes_state(self.REDIS_NES_STATE_BAD)
            return False

    def _check_entitlement_status(self, entitlement_id, customer_id):
        try:
            url = self._entitlement_url.format(customer_id, entitlement_id)
            response = requests.get(url, headers=self._headers)

            # If the credentials aren't accepted, update the JWT and try again
            if response.status_code in [401, 403]:
                self._headers.update({'Authorization': f'sso-jwt {self._get_jwt(self._cert)}'})
                response = requests.get(url, headers=self._headers)

            # If the response is 200, parse the response for the desired status
            if response.status_code == 200:
                resp_dict = response.json()
                entitlement_status = resp_dict.get('status')
                #    MESSAGE = "Requested {} on entitlement ID: {}, customer ID: {}.  Status = {}.  Message = {}"
                self._logger.info(self.MESSAGE.format('entitlement data', entitlement_id, customer_id, 'Success!', f'status = {entitlement_status}'))
                return entitlement_status

            # If the response is anything else, log the error, and return false
            error_msg = self.MESSAGE.format('entitlement data', entitlement_id, customer_id, f'POST request returned error {response.status_code}', response.text)
            self._logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = self.MESSAGE.format('entitlement data', entitlement_id, customer_id, 'Exception thrown!', e)
            self._logger.exception(error_msg)
            return error_msg

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
            self._logger.exception(e)
