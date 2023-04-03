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
    REDIS_SHOPPER_ID_PREFIX = 'shopper-id-key'

    def __init__(self, app_settings):
        self._shopper_api_url = app_settings.SHOPPER_API_URL
        self._redis = Redis(app_settings.REDIS)
        self._cert = (app_settings.ZEUS_CLIENT_CERT, app_settings.ZEUS_CLIENT_KEY)
        self._logger = logging.getLogger(__name__)

    def get_customer_id_from_shopper_id(self, shopper_id):
        """
        Given a ShopperID, retrieve the customerID
        """
        if not shopper_id:
            return

        redis_key = f'{self.REDIS_SHOPPER_ID_PREFIX}-{shopper_id}'
        customer_id = self._redis.get(redis_key)
        if customer_id:
            return customer_id.decode()

        try:
            url = f'{self._shopper_api_url}/v1/shoppers/{shopper_id}'
            params = {'includes': 'contact,preference', 'auditClientIp': 'zeus'}
            resp = requests.get(url, params=params, cert=self._cert)
            resp.raise_for_status()
            data = resp.json()
            customer_id = data['customerId']
            self._redis.setex(redis_key, self.REDIS_EXPIRATION, customer_id)
            return customer_id
        except Exception as e:
            self._logger.error(f'Error in getting the shopper info for {shopper_id} : {e}')
        return

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
            url = f'{self._shopper_api_url}/v1/customers/{customer_id}/shopper'
            resp = requests.get(url, params=self.SHOPPER_PARAMS, cert=self._cert)
            resp.raise_for_status()
            data = json.loads(resp.text)
            shopper_id = data[self.KEY_SHOPPER_ID]
            self._redis.setex(redis_key, self.REDIS_EXPIRATION, shopper_id)
            return shopper_id
        except Exception as e:
            self._logger.error(f'Error in getting the shopperID: {e}')
        return

    def get_shopper_id_from_dict(self, data):
        if isinstance(data, dict):
            parent_child_list = get_parent_child_shopper_ids_from_dict(data)
            if not parent_child_list:
                customer_id = data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('customerId', None)
                if customer_id:
                    return self.get_shopper_id_from_customer_id(customer_id)
                return data.get('data', {}).get('domainQuery', {}).get('shopperInfo', {}).get('shopperId', None)
            else:
                if parent_child_list.get('child_shopper_id'):
                    return parent_child_list.get('child_shopper_id')
                return self.get_shopper_id_from_customer_id(parent_child_list.get('child_customer_id'))
        return None

    def get_host_shopper_id_from_dict(self, data):
        #  The host customerId / shopperId field currently appear in...
        #    1: data->domainQuery->host->[shopperId or customerId]
        customer_id = data.get('data', {}).get('domainQuery', {}).get('host', {}).get('customerId', None)
        if customer_id:
            return self.get_shopper_id_from_customer_id(customer_id)
        return data.get('data', {}).get('domainQuery', {}).get('host', {}).get('shopperId', None)

    def get_list_of_ids_to_notify(self, data):
        # If the domain is associated with a parent/child API reseller account, then email both the parent and child
        # shopperIDs after converting from customerIDs, if needed.
        shopper_id_list = []
        parent_child_list = get_parent_child_shopper_ids_from_dict(data)
        if not parent_child_list:
            shopper_id = self.get_shopper_id_from_dict(data)
            if shopper_id:
                shopper_id_list.append(shopper_id)
        else:
            if parent_child_list.get('parent_customer_id'):
                shopper_id_list.append(
                    self.get_shopper_id_from_customer_id(parent_child_list.get('parent_customer_id')))
                shopper_id_list.append(self.get_shopper_id_from_customer_id(parent_child_list.get('child_customer_id')))
            else:
                shopper_id_list.append(parent_child_list.get('parent_shopper_id'))
                shopper_id_list.append(parent_child_list.get('child_shopper_id'))
        return shopper_id_list
