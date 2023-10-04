# TODO CMAPT-5272: delete this entire file
import logging

import requests
from requests.packages.urllib3.exceptions import (InsecurePlatformWarning,
                                                  InsecureRequestWarning)

from settings import AppConfig
from zeus.events.suspension.interface import Product

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)


class MWPOne(Product):
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def __init__(self, app_settings: AppConfig):
        self._logger = logging.getLogger('celery.tasks')
        self.mwpv3_url = app_settings.MWPV3_URL
        self.cert = (app_settings.ZEUS_CLIENT_CERT, app_settings.ZEUS_CLIENT_KEY)
        self.sso_url = app_settings.SSO_URL

    def _get_shopper_jwt(self, shopper_id: str) -> str:
        response = requests.post(f'{self.sso_url}/secure/api/delegation',
                                 json={
                                     'subordinate_user': shopper_id,
                                     'realm': 'idp'
                                 }, cert=self.cert)
        response.raise_for_status()
        return response.json()['data']

    def perform_action(self, guid: str, data: dict, shopper_id: str, action: str):
        url = f'{self.mwpv3_url}/api/v1/mwp/sites/{guid}'
        try:
            response = requests.post(url=url,
                                     headers={'Authorization': f'sso-jwt {self._get_shopper_jwt(shopper_id)}'},
                                     json={
                                         'action': action
                                     })
            response.raise_for_status()
            response_json = response.json()
            if (response_json['successful']):
                return True

        except Exception as e:
            self._logger.exception(f'Failed to suspend account {guid}. {e}')
        return False

    def suspend(self, guid, data, **kwargs):
        shopper_id = data.get('data', {}).get('domainQuery', {}).get('host', {}).get('shopperId', None)
        return self.perform_action(guid, data, shopper_id, 'suspendAccount')

    def reinstate(self, guid, data, **kwargs):
        shopper_id = data.get('data', {}).get('domainQuery', {}).get('host', {}).get('shopperId', None)
        return self.perform_action(guid, data, shopper_id, 'unsuspendAccount')

    def cancel(self):
        pass

    def block_content(self):
        pass

    def unblock_content(self):
        pass

    def delete_content(self):
        pass
