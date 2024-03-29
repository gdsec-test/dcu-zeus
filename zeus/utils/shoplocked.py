import logging
import os

import requests


class Shoplocked:
    _headers = {'Content-Type': 'application/json'}

    def __init__(self, app_settings):
        self._logger = logging.getLogger('celery.tasks')
        self._shoplocked_url = app_settings.SHOPLOCKED_URL
        self._sso_url = app_settings.SSO_URL
        self._sso_endpoint = app_settings.SSO_URL + '/v1/secure/api/token'

        self.env = os.getenv('sysenv', 'dev')
        self._cert = (app_settings.ZEUS_CLIENT_CERT, app_settings.ZEUS_CLIENT_KEY)
        self._headers.update({'Authorization': f'sso-jwt {self._get_jwt(self._cert)}'})

    def scrambler(self, shopper_id, note):
        """
         Scramble credentials for the given shopper_id. API deets: https://github.com/gdcorp-infosec/dcu-shoplocked

         :param shopper_id: Shopper account ID
         :param note: CRM note about why the account was locked or what further actions to be taken etc
         :return:
        """

        # Scramble service is not available in OTE.
        if not self._shoplocked_url:
            self._logger.warning('Locking service not available')
            return

        endpoint = self._shoplocked_url + '/scramblePassword'
        body = {'note': note, 'creds': [shopper_id]}

        try:
            response = requests.post(endpoint, json=body, headers=self._headers, verify=True)
            if response.status_code in [401, 403]:
                self._headers.update({'Authorization': f'sso-jwt {self._get_jwt(self._cert)}'})
                response = requests.post(endpoint, json=body, headers=self._headers, verify=True)

            if response.status_code != 201:
                self._logger.warning(
                    'Failed to scramble creds for shopper ID: {}, Status code: {}, Message: {}'.format(
                        shopper_id, response.status_code, response.json().get('message', {})))
            else:
                # Status code 201 is returned for success as well as failed scrambling.
                json_data = response.json()

                if json_data.get('failed'):
                    self._logger.warning(f'Failed to scramble creds for shopper ID: {shopper_id}')
                elif json_data.get('success'):
                    self._logger.info(f'Successfully scramble creds for shopper ID: {shopper_id}')
        except Exception as e:
            self._logger.error(f'Failed to scramble creds for shopper ID with exception: {e}')

    def _get_jwt(self, cert):
        """
        Attempt to retrieve the JWT associated with the cert/key pair from SSO
        :param cert:
        :return:
        """
        try:
            response = requests.post(self._sso_endpoint, data={'realm': 'cert'}, cert=cert)
            response.raise_for_status()

            body = response.json()
            return body.get('data')  # {'type': 'signed-jwt', 'id': 'XXX', 'code': 1, 'message': 'Success', 'data': JWT}
        except Exception as e:
            self._logger.error(e)
        return None
