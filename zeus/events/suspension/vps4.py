import json
import logging

import requests

from zeus.events.suspension.interface import Product
from zeus.utils.functions import get_host_info_from_dict


class VPS4(Product):
    _headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self._vps4_urls = app_settings.VPS4_URLS
        self._vps4_user = app_settings.VPS4USER
        self._vps4_pass = app_settings.VPS4PASS

        self._sso_endpoint = app_settings.SSO_URL + '/v1/api/token'

        self._headers['Authorization'] = f'sso-jwt {self._get_jwt()}'

    def _require_jwt_refresh(self, response):
        """
        Attempt to refresh the JWT associated with the service account creds from SSO
        :param response:
        :return:
        """
        if response and response.status_code == 403 and response.json().get('id') == 'MISSING_AUTHENTICATION':
            self._headers['Authorization'] = "sso-jwt " + self._get_jwt()
            return True
        return False

    def _retrieve_credits(self, vps4_url, guid):
        credits_url = vps4_url + '/api/credits/' + guid
        credits_data = None

        try:
            response = requests.get(credits_url, headers=self._headers)

            if self._require_jwt_refresh(response):
                response = requests.get(credits_url, headers=self._headers)

            credits_data = response.json() if response.status_code == 200 else None

        except Exception as e:
            self._logger.error(f'Failed to retrieve credits data from server : {vps4_url} for guid : {guid}. Details: {e}')
        return credits_data

    def suspend(self, guid, data, **kwargs):
        self._logger.info(f'VPS4 suspend called for {guid}')

        if not guid:
            return False

        dc = get_host_info_from_dict(data).get('dataCenter')
        if dc in self._vps4_urls:
            if self._suspend(self._vps4_urls.get(dc), guid):
                return True

        # Fall back and try all data center urls.
        for dc_key, dc_url in list(self._vps4_urls.items()):
            if dc_key != dc and self._suspend(dc_url, guid):
                return True

        self._logger.error(f'Unable to suspend guid : {guid} using all 3 VPS4 urls')
        return False

    def _suspend(self, url, guid):
        max_retries = 10
        credits_data = self._retrieve_credits(url, guid)

        if credits_data:
            self._logger.info(f'Credits retrieved for {guid} and url {url}')

            vm_id = credits_data.get('productId')
            abuse_url = url + f'/api/vms/{vm_id}/abuseSuspend'

            try:
                response = requests.post(abuse_url, headers=self._headers)

                if self._require_jwt_refresh(response):
                    response = requests.post(abuse_url, headers=self._headers)

                while max_retries > 0 and response.status_code == 200:
                    credits_data = self._retrieve_credits(url, guid)
                    self._logger.info(f'Credits retrieved after suspension for {guid} and url {url}')

                    if credits_data.get('abuseSuspendedFlagSet'):
                        self._logger.info(f'Successfully suspended VPS4 guid {guid} on server {url}')
                        return True

                    max_retries -= 1

            except Exception as e:
                self._logger.error(f'Unable to suspend guid : {guid} using url : {url}. Details: {e}')

        return False

    def reinstate(self, **kwargs):
        pass

    def cancel(self):
        pass

    def block_content(self):
        pass

    def unblock_content(self):
        pass

    def delete_content(self):
        pass

    def _get_jwt(self):
        """
        Attempt to retrieve the JWT associated with the service account creds from SSO
        :return:
        """
        try:
            response = requests.post(self._sso_endpoint, data={'username': self._vps4_user, 'password': self._vps4_pass, 'realm': 'jomax'})
            response.raise_for_status()

            body = json.loads(response.text)
            # Expected return body.get {'type': 'signed-jwt', 'id': 'XXX', 'code': 1, 'message': 'Success', 'data': JWT}
            return body.get('data')
        except Exception as e:
            self._logger.error(e)
        return None
