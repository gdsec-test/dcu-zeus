import logging
import os
from datetime import timedelta
from typing import Optional

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
    REDIS_NES_STATE_BAD = 'DOWN'

    def __init__(self, settings: AppConfig):
        self._logger = logging.getLogger(__name__)

        self._subscriptions_url = settings.SUBSCRIPTIONS_URL
        self._entitlement_url = settings.ENTITLEMENT_URL
        self._sso_endpoint = settings.SSO_URL + '/v1/secure/api/token'
        self._cert = (settings.ZEUS_CLIENT_CERT, settings.ZEUS_CLIENT_KEY)

        self._headers.update({'Authorization': f'sso-jwt {self._get_jwt(self._cert)}'})

        # NOTE: if you switch this to StrictRedis, you MUST also update the call to 'setex' below.
        # In the version of redis we are currently using, the 'time' and 'value' parameters for 'setex' were flipped:
        #  value first, then time.  In other version of redis, as well as the StrictRedis the parameters are: time, then value.
        self._redis = Redis(settings.REDIS)

    def suspend(self, entitlement_id: str, customer_id: str, product: str) -> bool:
        return self._do_suspend_reinstate(entitlement_id, customer_id, self.SUSPEND_CMD, product)

    def reinstate(self, entitlement_id: str, customer_id: str, product: str) -> bool:
        return self._do_suspend_reinstate(entitlement_id, customer_id, self.REINSTATE_CMD, product)

    def get_nes_state(self) -> bool:
        nes_state = self._redis.get(self.REDIS_NES_STATE_KEY)
        if nes_state:
            state = nes_state.decode()
            return state != self.REDIS_NES_STATE_BAD
        # If the nes-state isn't set, assume that it is good
        return True

    def set_nes_state(self, state: str) -> None:
        if state == self.REDIS_NES_STATE_BAD:
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

    def _do_suspend_reinstate(self, entitlement_id: str, customer_id: str, url_cmd: str, product: str) -> bool:
        try:
            # Only perform the suspend / reinstate if it isn't already in that state
            status = self._get_entitlement_status(entitlement_id, customer_id, product)
            expected_status = 'SUSPENDED' if url_cmd == self.SUSPEND_CMD else 'ACTIVE'
            if status == expected_status:
                self._log_info(f'Account already has correct status of {status}', entitlement_id, customer_id, product_type=product)
                return True

            url = f'{self._subscriptions_url}v2/customers/{customer_id}/{url_cmd}'
            body = {'entitlementId': entitlement_id, 'suspendReason': self.SUSPEND_REASON}
            response = requests.post(url, json=body, headers=self._headers, timeout=30)

            # If these credentials aren't accepted, update the JWT and try again
            if response.status_code in [401, 403]:
                self._headers.update({'Authorization': f'sso-jwt {self._get_jwt(self._cert)}'})
                response = requests.post(url, json=body, headers=self._headers, timeout=30)

            # process response and log errors and successes
            if response.status_code not in [200, 204]:
                self.set_nes_state(self.REDIS_NES_STATE_BAD)
                self._log_error(f'Failed to perform {url_cmd}', entitlement_id, customer_id, response.status_code, response.text, product_type=product)
                return False
            else:
                self._log_info(f'Successfully performed {url_cmd}', entitlement_id, customer_id, product_type=product, status_code=response.status_code)
                return True

        except Exception as e:
            self._log_exception(f'Exception thrown while trying to perform {url_cmd}', e, entitlement_id, customer_id, product)
            self.set_nes_state(self.REDIS_NES_STATE_BAD)
            return False

    def _get_entitlement_status(self, entitlement_id: str, customer_id: str, product: str) -> str:
        try:
            url = f'{self._entitlement_url}v2/customers/{customer_id}/entitlements/{entitlement_id}'
            response = requests.get(url, headers=self._headers, timeout=30)

            # If the credentials aren't accepted, update the JWT and try again
            if response.status_code in [401, 403]:
                self._headers.update({'Authorization': f'sso-jwt {self._get_jwt(self._cert)}'})
                response = requests.get(url, headers=self._headers, timeout=30)

            # If the response is 200, parse the response for the desired status
            if response.status_code == 200:
                json_response = response.json()
                entitlement_status = json_response.get('status')
                self._log_info(f'Got entitlement status {entitlement_status}', entitlement_id, customer_id, product_type=product, status_code=response.status_code)
                return entitlement_status

            # If the response is anything else, log the error, and return that error
            self.set_nes_state(self.REDIS_NES_STATE_BAD)
            error_msg = 'Failed to get entitlement status'
            self._log_error(error_msg, entitlement_id, customer_id, response.status_code, response.text, product)
            return error_msg
        except Exception as e:
            self.set_nes_state(self.REDIS_NES_STATE_BAD)
            error_msg = 'Exception thrown while trying to get entitlement status'
            self._log_exception(error_msg, e, entitlement_id, customer_id, product_type=product)
            return error_msg

    def _log_error(self, message: str, entitlement_id: str, customer_id: str, status_code: int, response_msg: str, product_type: Optional[str]) -> None:
        extraData = {
            'entitlementId': entitlement_id,
            'customerId': customer_id,
            'statusCode': status_code,
            'responseMsg': response_msg
        }
        if product_type:
            extraData.update({'productType': product_type})
        self._logger.error(message, extra=extraData)

    def _log_info(self, message: str, entitlement_id: str, customer_id: str, product_type: Optional[str], status_code: Optional[int] = None) -> None:
        extraData = {
            'entitlementId': entitlement_id,
            'customerId': customer_id}
        if status_code:
            extraData.update({'statusCode': str(status_code)})
        if product_type:
            extraData.update({'productType': product_type})
        self._logger.info(message, extra=extraData)

    def _log_exception(self, message: str, e: Exception, entitlement_id: str, customer_id: str, product_type: Optional[str]) -> None:
        extraData = {
            'exception': e,
            'entitlement_id': entitlement_id,
            'customer_id': customer_id
        }
        if product_type:
            extraData.update({'productType': product_type})
        self._logger.exception(message, extra=extraData)

    def _get_jwt(self, cert: tuple) -> str:
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
            return ''
