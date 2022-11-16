# TODO CMAPT-5272: delete this entire file
import json
import logging

import requests

from zeus.events.suspension.interface import Product


class Vertigo(Product):
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def __init__(self, app_settings):
        self._logger = logging.getLogger('celery.tasks')
        self.url = app_settings.VERT_URL
        self._auth = (app_settings.VERTIGO_USER, app_settings.VERTIGO_PASS)

    def suspend(self, guid, data, **kwargs):
        cid = data.get('data', {}).get('domainQuery', {}).get('host', {}).get('containerId', '')
        url = self.url + cid + '/?suspend'

        try:
            body = json.dumps({'reason': 'DCU Suspension'}, ensure_ascii=False)

            response = requests.post(url, auth=self._auth, headers=self.headers, data=body)
            response.raise_for_status()

            return response.status_code == 202

        except Exception as e:
            self._logger.error(f'Failed to suspend GUID: {guid}. {e}')
        return False

    def reinstate(self):
        pass

    def cancel(self):
        pass

    def block_content(self):
        pass

    def unblock_content(self):
        pass

    def delete_content(self):
        pass
