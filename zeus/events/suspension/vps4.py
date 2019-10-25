import json
import logging

import requests

from zeus.events.suspension.interface import Product


class VPS4(Product):
    _headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self._vps4_urls = app_settings.VPS4_URLS
        self._vps4_user = app_settings.VPS4USER
        self._vps4_pass = app_settings.VPS4PASS

        self._sso_endpoint = app_settings.SSO_URL + '/v1/api/token'

        self._headers['Authorization'] = 'sso-jwt {}'.format(self._get_jwt())

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

        try:
            response = requests.get(credits_url, headers=self._headers)

            if self._require_jwt_refresh(response):
                response = requests.get(credits_url, headers=self._headers)

            return response.json() if response.status_code == 200 else None
        except Exception as e:
            self._logger.error("Failed to retrieve credits data from server : {} for guid : {}. Details: {}"
                               .format(vps4_url, guid, e.message))

    def suspend(self, guid, **kwargs):
        max_retries = 10

        if not guid:
            return False

        self._logger.info("VPS4 suspend called for {}".format(guid))

        for url in self._vps4_urls:
            credits_data = self._retrieve_credits(url, guid)
            if credits_data:
                self._logger.info("Credits retrieved for {} and url {}".format(guid, url))
                vm_id = credits_data.get('productId')
                abuse_url = url + '/api/vms/{}/abuseSuspend'.format(vm_id)

                try:
                    response = requests.post(abuse_url, headers=self._headers)

                    if self._require_jwt_refresh(response):
                        response = requests.post(abuse_url, headers=self._headers)

                    while max_retries > 0 and response.status_code == 200:
                        credits_data = self._retrieve_credits(url, guid)
                        self._logger.info("Credits retrieved after suspension for {} and url {}".format(guid, url))
                        if credits_data.get('abuseSuspendedFlagSet'):
                            self._logger.info("Successfully suspended VPS4 guid {} on server {}".format(guid, url))
                            return True
                        max_retries -= 1

                except Exception as e:
                    self._logger.error("Unable to suspend guid : {} using url : {}. Details: {}".format(guid, url, e.message))

        self._logger.error("Unable to suspend guid : {} using all 3 VPS4 urls".format(guid))
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
