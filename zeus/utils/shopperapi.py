import json
import logging
from datetime import timedelta

import requests
from redis import Redis

from zeus.utils.functions import get_parent_child_shopper_ids_from_dict


class ShopperAPI:
    SHOPPER_PARAMS = {'auditClientIp': 'zeus.client.cest.int.gdcorp.tools'}
    KEY_SHOPPER_ID = 'shopperId'
    REDIS_EXPIRATION = timedelta(days=5)
    REDIS_CUSTOMER_ID_PREFIX = 'customer-id-key'

    def __init__(self, app_settings):
        self._customer_url = app_settings.CUSTOMER_URL

        self._redis = Redis(app_settings.REDIS)
        self._cert = (app_settings.ZEUS_CLIENT_CERT, app_settings.ZEUS_CLIENT_KEY)
        self._logger = logging.getLogger(__name__)

    def get_shopper_id_from_customer_id(self, customer_id):
        """
        Take a customerID get the associated shopperID.
        """
        if not customer_id:
            return

        self._logger.info('Checking redis for shopper ID')
        redis_key = f'{self.REDIS_CUSTOMER_ID_PREFIX}-{customer_id}'
        self._logger.info(f'Redis command is: {redis_key}')
        shopper_id = self._redis.get(redis_key)
        self._logger.info(f'raw shopper ID from redis is: {shopper_id}')
        if shopper_id:
            self._logger.info(f'decoded shopper ID from redis is {shopper_id.decode()}')
            return shopper_id.decode()

        try:
            self._logger.info('Getting shopperID from shopper API')
            resp = requests.get(self._customer_url.format(customer_id), params=self.SHOPPER_PARAMS, cert=self._cert)
            resp.raise_for_status()
            data = json.loads(resp.text)
            shopper_id = data[self.KEY_SHOPPER_ID]
            self._logger.info(f'Shopper ID from shopper API is {shopper_id}')
            self._redis.setex(redis_key, self.REDIS_EXPIRATION, shopper_id)
            return shopper_id
        except Exception as e:
            self._logger.error(f'Error in getting the shopperID: {e}')
        return

    def get_shopper_id_from_dict(self, data):
        customer_id = data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('customerId', None)
        self._logger.info(f'In get_shopper_id_from_dict.  customer_id value from data was {customer_id}')
        if customer_id:
            return self.get_shopper_id_from_customer_id(customer_id)
        shopper_id = data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('shopperId', None)
        self._logger.info(f'No customer ID found, shopperId from data was {shopper_id}')
        return data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('shopperId', None)

    def get_host_shopper_id_from_dict(self, data):
        #  The host customerId / shopperId field currently appear in...
        #    1: data->domainQuery->host->[shopperId or customerId]
        customer_id = data.get('data', {}).get('domainQuery', {}).get('host', {}).get('customerId', None)
        if customer_id:
            return self.get_shopper_id_from_customer_id(customer_id)
        return data.get('data', {}).get('domainQuery', {}).get('host', {}).get('shopperId', None)

    def get_list_of_ids_to_notify(self, data):
        # If the domain is associated with a parent/child API reseller
        #  account, then email both the parent and child account
        account_number_list = []
        parent_child_list = get_parent_child_shopper_ids_from_dict(data)
        if not parent_child_list:
            shopper_id = self.get_shopper_id_from_dict(data)
            if shopper_id:
                account_number_list.append(shopper_id)
        else:
            # TODO: CMAPT-5231 - uncomment this code and remove line 72 because once apiReseller
            #       has been updated to save customerID, we need to convert that to a shopperID
            # for customer_id in parent_child_list:
            #     account_number_list.append(self.get_shopper_id_from_customer_id(customer_id))
            account_number_list = parent_child_list
        return account_number_list
