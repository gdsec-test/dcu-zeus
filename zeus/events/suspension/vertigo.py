import json
import logging

import requests

from zeus.events.suspension.interface import Product


class Vertigo(Product):
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self.url = app_settings.VERT_URL
        self.auth = (app_settings.VERTIGOUSER, app_settings.VERTIGOPASS)

    def suspend(self, guid, data, **kwargs):
        cid = data.get('data', {}).get('domainQuery', {}).get('host', {}).get('containerID', '')
        url = self.url + cid + '/?suspend'

        try:
            body = json.dumps({'reason': 'DCU Suspension'}, ensure_ascii=False)

            response = requests.post(url, auth=self.auth, headers=self.headers, data=body, verify=False)
            response.raise_for_status()

            return response.status_code == 202

        except Exception as e:
            self._logger.error("Failed to suspend GUID: {}. {}".format(guid, e.message))
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
