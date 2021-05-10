import json
import logging

import requests


class Shoplocked:
    _headers = {'Content-Type': 'application/json'}

    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self._shoplocked_url = app_settings.SHOPLOCKED_URL
        self._sso_endpoint = app_settings.SSO_URL + '/v1/secure/api/token'

        cert = (app_settings.ZEUS_SSL_CERT, app_settings.ZEUS_SSL_KEY)
        self._headers.update({'Authorization': 'sso-jwt {}'.format(self._get_jwt(cert))})

    def adminlock(self, shopper_id, note):
        """
         Place an admin lock on the given shopper_id. API deets: https://github.secureserver.net/digital-crimes/shoplocked

         :param shopper_id: Shopper account ID
         :param note: CRM note about why the account was locked or what further actions to be taken etc
         :return:
        """

        # Shoplocked Locking service is not available in OTE.
        if not self._shoplocked_url:
            self._logger.warning('Locking service not available')
            return

        endpoint = self._shoplocked_url + '/lockAdmin'
        body = {'note': note, 'creds': [shopper_id]}

        try:
            response = requests.post(endpoint, json=body, headers=self._headers, verify=False)

            if response.status_code != 201:
                self._logger.warning('Failed to admin lock shopper ID: {}, Status code: {}, Message: {}'.format(
                    shopper_id, response.status_code, response.json().get('message', {})))
            else:
                # Status code 201 is returned for success as well as failed locking.
                json_data = json.loads(response.text)

                if json_data.get('failed'):
                    self._logger.warning(f'Failed to admin lock shopper ID: {shopper_id}')
                elif json_data.get('success'):
                    self._logger.info(f'Successfully admin locked shopper ID: {shopper_id}')
        except Exception as e:
            self._logger.error(f'Failed to admin lock shopper ID with exception: {e}')

    def _get_jwt(self, cert):
        """
        Attempt to retrieve the JWT associated with the cert/key pair from SSO
        :param cert:
        :return:
        """
        try:
            response = requests.post(self._sso_endpoint, data={'realm': 'cert'}, cert=cert)
            response.raise_for_status()

            body = json.loads(response.text)
            return body.get('data')  # {'type': 'signed-jwt', 'id': 'XXX', 'code': 1, 'message': 'Success', 'data': JWT}
        except Exception as e:
            self._logger.error(e)
        return None
