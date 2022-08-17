import json
import logging

import requests
from csetutils.appsec.logging import get_logging

from zeus.events.suspension.interface import Product


class Vertigo(Product):
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def __init__(self, app_settings):
        self._logger = logging.getLogger('celery.tasks')
        self.url = app_settings.VERT_URL
        self._auth = (app_settings.CMAP_PROXY_USER, app_settings.CMAP_PROXY_PASS)
        self._cert = (app_settings.CMAP_PROXY_CERT, app_settings.CMAP_PROXY_KEY)

    def suspend(self, guid, data, **kwargs):
        cid = data.get('data', {}).get('domainQuery', {}).get('host', {}).get('containerId', '')
        url = self.url + cid + '/?suspend'

        try:
            body = json.dumps({'reason': 'DCU Suspension'}, ensure_ascii=False)

            response = requests.post(url, cert=self._cert, auth=self._auth, headers=self.headers, data=body,
                                     verify=False)
            response.raise_for_status()
            appseclogger = get_logging("dev", "zeus")
            container_id = data.get('data', {}).get('domainQuery', {}).get('host', {}).get('containerId', '')
            appseclogger.info("suspending vertigo product", extra={"event": {"kind": "event",
                                                                             "category": "process",
                                                                             "type": ["change", "user"],
                                                                             "outcome": "success",
                                                                             "action": "suspend"},
                                                                   "suspension":
                                                                       {"guid": guid,
                                                                        "product": "Vertigo",
                                                                        "container_id": container_id}})

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
