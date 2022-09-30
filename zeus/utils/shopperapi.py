import json
from datetime import timedelta

import requests
from redis import Redis

from zeus.utils.functions import get_parent_child_shopper_ids_from_dict


class ShopperAPI:
    SHOPPER_PARAMS = {'auditClientIp': 'cmap.service.int.godaddy.com'}
    KEY_SHOPPER_ID = 'shopperId'
    REDIS_EXPIRATION = timedelta(days=5)

    def __init__(self, app_settings):
        self._shopper_url = app_settings.SHOPPER_URL
        self._customer_url = app_settings.CUSTOMER_URL

        self.redis = Redis(app_settings.REDIS)
        self._cert = (app_settings.ZEUS_CLIENT_CERT, app_settings.ZEUS_CLIENT_KEY)

    def get_shopper_id_from_customer_id(self, customer_id):
        """
        Take a customerID get the associated shopperID.
        """
        if not customer_id:
            return

        redis_key = f'{self.REDIS_CUSTOMER_ID_PREFIX}-{customer_id}'
        shopper_id = self._redis.get(redis_key)
        if shopper_id:
            return shopper_id.decode()

        try:
            resp = requests.get(self._customer_url.format(customer_id), params=self.SHOPPER_PARAMS, cert=self._cert)
            resp.raise_for_status()
            data = json.loads(resp.text)
            shopper_id = data[self.KEY_SHOPPER_ID]
            self._redis.setex(redis_key, self.REDIS_EXPIRATION, shopper_id)
            return shopper_id
        except Exception as e:
            self._logger.error(f'Error in getting the shopperID: {e}')
        return

    def get_shopper_id_from_dict(self, data):
        shopper_id = data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('shopperId', None)
        if not shopper_id:
            customer_id = data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('customerId', None)
            if not customer_id:
                shopper_id = self.get_shopper_id_from_customer_id(customer_id)
        return shopper_id

    def get_host_shopper_id_from_dict(self, data):
        #  The host shopperId field currently appears in...
        #    1: data->domainQuery->host->shopperId
        shopper_id = data.get('data', {}).get('domainQuery', {}).get('host', {}).get('shopperId', None)
        if not shopper_id:
            customer_id = data.get('data', {}).get('domainQuery', {}).get('host', {}).get('customerId', None)
            if not customer_id:
                shopper_id = self.get_shopper_id_from_customer_id(customer_id)
        return shopper_id

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
            account_number_list = parent_child_list
        return account_number_list
