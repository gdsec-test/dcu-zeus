import logging
import os
import time
from datetime import datetime, timedelta
from typing import List

import elasticapm
import requests
from redis import Redis

from settings import AppConfig
from zeus.utils.functions import get_host_info_from_dict


class NESHelper():
    _headers = {'Content-Type': 'application/json', 'x-app-key': 'zeus'}
    SUSPEND_REASON = 'POLICY'  # POLICY - means it's being suspended for ABUSE

    SUSPEND_CMD = 'suspendByEntitlementId'
    REINSTATE_CMD = 'reinstateByEntitlementId'

    VALID_ENTITLEMENT_STATUSES = ['ACTIVE', 'SUSPENDED', 'PEND_CANCEL', 'CANCELLED']

    REDIS_EXPIRATION = timedelta(minutes=10)
    REDIS_NES_STATE_KEY = 'nes-state'
    REDIS_NES_STATE_GOOD = 'UP'
    REDIS_NES_STATE_BAD = 'DOWN'

    def __init__(self, settings: AppConfig):
        self._logger = logging.getLogger(__name__)

        self._nes_url = settings.SUBSCRIPTIONS_URL
        self._entitlement_url = settings.ENTITLEMENT_URL
        self._sso_endpoint = settings.SSO_URL + '/v1/secure/api/token'
        self._cert = (settings.ZEUS_CLIENT_CERT, settings.ZEUS_CLIENT_KEY)

        self._headers.update({'Authorization': f'sso-jwt {self._get_jwt(self._cert)}'})

        # NOTE: if you switch this to StrictRedis, you MUST also update the call to 'setex' below.
        # In the version of redis we are currently using, the 'time' and 'value' parameters for 'setex' were flipped:
        #  value first, then time.  In other version of redis, as well as the StrictRedis the parameters are: time, then value.
        self._redis = Redis(settings.REDIS)

    def suspend(self, entitlement_id: str, customer_id: str) -> bool:
        # If suspension succeeded, poll for entitlement status
        if(self._do_suspend_reinstate(entitlement_id, customer_id, self.SUSPEND_CMD)):
            return self.wait_for_entitlement_status(entitlement_id, customer_id, 'SUSPENDED')
        return False

    def reinstate(self, entitlement_id: str, customer_id: str) -> bool:
        # If reinstatement succeeded, poll for entitlement status
        if(self._do_suspend_reinstate(entitlement_id, customer_id, self.REINSTATE_CMD)):
            return self.wait_for_entitlement_status(entitlement_id, customer_id, 'ACTIVE')
        return False

    def get_nes_state(self) -> bool:
        nes_state = self._redis.get(self.REDIS_NES_STATE_KEY)
        if nes_state:
            state = nes_state.decode()
            return state == self.REDIS_NES_STATE_GOOD
        # If the nes-state isn't set, assume that it is good
        return True

    def set_nes_state(self, state: str) -> None:
        client = elasticapm.get_client()
        if client:
            client.capture_message(f'NES state is {state}')
        self._redis.setex(self.REDIS_NES_STATE_KEY, state, self.REDIS_EXPIRATION)

    # TODO CMAPT-5272: remove this function and all calls to it
    def get_use_nes(self, data: dict) -> bool:
        # TODO CMAPT-5272: remove the NES selection flags
        products_use_nes_flag = {
            'diablo': os.environ.get('DIABLO_USE_NES', None),
            'vertigo': os.environ.get('VERTIGO_USE_NES', None),
            'mwp 1.0': os.environ.get('MWPONE_USE_NES', None),
            'plesk': os.environ.get('ANGELO_USE_NES', None),
            'vps4': os.environ.get('VPS4_USE_NES', None),
            'gocentral': os.environ.get('GOCENTRAL_USE_NES', None)
        }
        all_use_nes_flag = os.environ.get('ALL_USE_NES', None)

        # Only check if we should use NES if this is a hosted product
        hosted_status = data.get('hosted_status') or data.get('hostedStatus')
        if hosted_status == 'HOSTED':
            product = get_host_info_from_dict(data).get('product', '').lower()
            if product:
                return products_use_nes_flag.get(product) == 'True' or all_use_nes_flag == 'True'
        return False

    def wait_for_entitlement_status(self, entitlement_id: str, customer_id: str, status: str) -> bool:
        start_time = datetime.now()
        current_time = datetime.now()
        time_diff = current_time - start_time
        while time_diff.total_seconds() < 600:
            time.sleep(1)
            status_response = self._check_entitlement_status(entitlement_id, customer_id)
            # If the response from 'check entitlement status' is not one of the valid statuses, then we know an error happened.  Return False
            if status_response not in self.VALID_ENTITLEMENT_STATUSES:
                return False
            # If the resposne is the status we are looking for, return true
            if status_response == status:
                self._log_info('Entitlement status successfully updated', entitlement_id, customer_id)
                self._logger.info(f'Entitlement status wait took {time_diff} seconds')
                return True
            current_time = datetime.now()
            time_diff = current_time - start_time
        return False

    def _do_suspend_reinstate(self, entitlement_id: str, customer_id: str, url_cmd: str) -> bool:
        try:
            # Only perform the suspend / reinstate if it isn't already in that state
            status = self._check_entitlement_status(entitlement_id, customer_id)
            expected_status = 'SUSPENDED' if url_cmd == self.SUSPEND_CMD else 'ACTIVE'
            if status == expected_status:
                self._log_info(f'Account already has correct status of {status}', entitlement_id, customer_id)
                return True

            url = f'{self._nes_url}v2/customers/{customer_id}/{url_cmd}'
            body = {'entitlementId': entitlement_id, 'suspendReason': self.SUSPEND_REASON}
            response = requests.post(url, json=body, headers=self._headers, timeout=30)

            # If these credentials aren't accepted, update the JWT and try again
            if response.status_code in [401, 403]:
                self._headers.update({'Authorization': f'sso-jwt {self._get_jwt(self._cert)}'})
                response = requests.post(url, json=body, headers=self._headers, timeout=30)

            # process response and log errors and successes
            if response.status_code not in [200, 204]:
                self.set_nes_state(self.REDIS_NES_STATE_BAD)
                self._log_error(f'Failed to perform {url_cmd}', entitlement_id, customer_id, response.status_code, response.text)
                return False
            else:
                self.set_nes_state(self.REDIS_NES_STATE_GOOD)
                self._log_info(f'Successfully performed {url_cmd}', entitlement_id, customer_id)
                return True

        except Exception as e:
            self._log_exception(f'Exception thrown while trying to perform {url_cmd}', e, entitlement_id, customer_id)
            self.set_nes_state(self.REDIS_NES_STATE_BAD)
            return False

    def _check_entitlement_status(self, entitlement_id: str, customer_id: str) -> str:
        try:
            url = f'{self._entitlement_url}v2/customers/{customer_id}/entitlements/{entitlement_id}'
            response = requests.get(url, headers=self._headers, timeout=30)

            # If the credentials aren't accepted, update the JWT and try again
            if response.status_code in [401, 403]:
                self._headers.update({'Authorization': f'sso-jwt {self._get_jwt(self._cert)}'})
                response = requests.get(url, headers=self._headers, timeout=30)

            # If the response is 200, parse the response for the desired status
            if response.status_code == 200:
                self.set_nes_state(self.REDIS_NES_STATE_GOOD)
                json_response = response.json()
                entitlement_status = json_response.get('status')
                self._log_info(f'Succesfully got entitlement status {entitlement_status}', entitlement_id, customer_id)
                return entitlement_status

            # If the response is anything else, log the error, and return that error
            self.set_nes_state(self.REDIS_NES_STATE_BAD)
            error_msg = 'Failed to get entitlement status'
            self._log_error(error_msg, entitlement_id, customer_id, response.status_code, response.text)
            return error_msg
        except Exception as e:
            error_msg = 'Exception thrown while trying to get entitlement status'
            self._log_exception(error_msg, e, entitlement_id, customer_id)
            return error_msg

    def _log_error(self, message: str, entitlement_id: str, customer_id: str, status_code: int, response_msg: str) -> None:
        self._logger.error(message, extra={
            'entitlementId': entitlement_id,
            'customerId': customer_id,
            'statusCode': status_code,
            'responseMsg': response_msg
        })

    def _log_info(self, message: str, entitlement_id: str, customer_id: str) -> None:
        self._logger.info(message, extra={
            'entitlementId': entitlement_id,
            'customerId': customer_id
        })

    def _log_exception(self, message: str, e: Exception, entitlement_id: str, customer_id: str) -> None:
        self._logger.exception(message, extra={
            'exception': e,
            'entitlement_id': entitlement_id,
            'customer_id': customer_id
        })

    def _get_jwt(self, cert: List[str]) -> str:
        """
        Attempt to retrieve the JWT associated with the cert/key pair from SSO
        :param cert: tuple of cert, key
        :return: JWT string or None
        """
        try:
            response = requests.post(self._sso_endpoint, data={'realm': 'cert'}, cert=cert)
            response.raise_for_status()

            body = response.json()
            return body.get('data')  # {'type': 'signed-jwt', 'id': 'XXX', 'code': 1, 'message': 'Success', 'data': JWT}
        except Exception as e:
            self._logger.exception(e)
