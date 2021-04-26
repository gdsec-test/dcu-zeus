import json
import logging

import requests
from requests.packages.urllib3.exceptions import (InsecurePlatformWarning,
                                                  InsecureRequestWarning)

from zeus.events.suspension.interface import Product
from zeus.utils.functions import get_host_shopper_id_from_dict

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)


class Angelo(Product):
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self.auth = (app_settings.PLESKUSER, app_settings.PLESKPASS)
        self.url = app_settings.PLESK_URL

    def suspend(self, guid, data, **kwargs):
        """
        :param guid: plesk guid
        :param data:
        :return: True if suspended or False if not
        """
        return self._suspend_or_reinstate(guid, data, '?suspend')

    def reinstate(self, guid, data, **kwargs):
        """
        :param guid: plesk guid
        :param data:
        :return: True if reinstated or False if not
        """
        return self._suspend_or_reinstate(guid, data, '?reinstate')

    def cancel(self):
        pass

    def block_content(self):
        pass

    def unblock_content(self):
        pass

    def delete_content(self):
        pass

    def _suspend_or_reinstate(self, guid, data, flag):
        """
        :param guid: plesk guid
        :param data:
        :param flag: ?suspend or ?reinstate
        :return: True if post succeeded or False if post failed
        """
        url = self.url + get_host_shopper_id_from_dict(data) + '/' + guid + flag

        try:
            body = json.dumps({'disable_panel': 'true', 'reason': 'DCU Abuse', 'type': 'abuse'}, ensure_ascii=False)

            response = requests.post(url, auth=self.auth, headers=self.headers, data=body, verify=False)
            response.raise_for_status()

            return response.status_code == 200

        except Exception as e:
            self._logger.error("Failed to {} GUID {}. {}".format(flag[1:], guid, e.message))
        return False
