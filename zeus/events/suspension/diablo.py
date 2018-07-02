import json
import logging

import requests
from requests.packages.urllib3.exceptions import InsecurePlatformWarning, InsecureRequestWarning

from zeus.events.suspension.interface import Product

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)


class Diablo(Product):
    def __init__(self, app_settings):
        self.url = app_settings.DIABLO_URL
        self.auth = (app_settings.DIABLOUSER, app_settings.DIABLOPASS)
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}

    def suspend(self, guid):
        """
        Waiting on user perm update by Diablo Dev for this to work
        :return:
        """

        body = json.dumps({"reason": "testing HA suspension", "type": "abuse", "enable_ftp": True}, ensure_ascii=False)

        try:
            with requests.Session() as session:
                r = session.post(self.url + guid + '?suspend', auth=self.auth, headers=self.headers,
                                 data=body, verify=False)
            if r.status_code == 200:
                return True
            else:
                logging.error('Failed to suspend GUID: {}, request status code: {}').format(guid, r.status_code)

        except Exception as e:
            logging.error(e.message)
            return False

    def reinstate(self, guid):
        """
        Waiting on user perm update by Diablo Dev for this to work
        :return:
        """
        body = json.dumps({"reason": "testing HA suspension"}, ensure_ascii=False)

        try:
            with requests.session() as session:
                r = session.post(self.url + guid + '?reinstate', auth=self.auth, headers=self.headers,
                                 data=body, verify=False)
            if r.status_code == 200:
                return True
            else:
                logging.error('Failed to reisntate GUID: {}, request status code: {}').format(guid, r.status_code)

        except Exception as e:
            logging.error(e.message)
            return False

    def cancel(self):
        pass

    def block_content(self):
        pass

    def unblock_content(self):
        pass

    def delete_content(self):
        pass
