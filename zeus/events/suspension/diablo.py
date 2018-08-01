import json
import logging

import requests
from requests.packages.urllib3.exceptions import InsecurePlatformWarning, InsecureRequestWarning

from zeus.events.suspension.interface import Product

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)


class Diablo(Product):
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def __init__(self, app_settings):
        self.url = app_settings.DIABLO_URL
        self.auth = (app_settings.DIABLOUSER, app_settings.DIABLOPASS)

    def suspend(self, guid):
        url = self.url + guid + '?suspend'

        try:
            body = json.dumps({'reason': 'DCU Suspension', 'type': 'abuse', 'enable_ftp': True}, ensure_ascii=False)

            response = requests.post(url, auth=self.auth, headers=self.headers, data=body, verify=False)
            response.raise_for_status()

            return response.status_code == 200

        except Exception as e:
            logging.error("Failed to suspend GUID: {}. {}".format(guid, e.message))
        return False

    def reinstate(self, guid):
        """
        Waiting on user perm update by Diablo Dev for this to work
        :return:
        """
        url = self.url + guid + '?reinstate'

        try:
            body = json.dumps({'reason': 'DCU Reinstatement'}, ensure_ascii=False)

            response = requests.post(url, auth=self.auth, headers=self.headers, data=body, verify=False)
            response.raise_for_status()

            return response.status_code == 200

        except Exception as e:
            logging.error("Failed to reinstate GUID: {}. {}".format(guid, e.message))
        return False

    def cancel(self):
        pass

    def block_content(self):
        pass

    def unblock_content(self):
        pass

    def delete_content(self):
        pass
