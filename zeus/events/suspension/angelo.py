import json
import logging
import requests

from requests.packages.urllib3.exceptions import InsecurePlatformWarning, InsecureRequestWarning
from zeus.events.suspension.interface import Product
from zeus.utils.functions import get_host_shopper_id_from_dict

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)


class Angelo(Product):

    def __init__(self, app_settings):
        self.auth = (app_settings.PLESKUSER, app_settings.PLESKPASS)
        self.body = json.dumps({"disable_panel": "true", "reason": "DCU Abuse", "type": "abuse"}, ensure_ascii=False)
        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}
        self.url = app_settings.PLESK_URL

    def suspend(self, guid, data):
        """
        :param guid: plesk guid
        :param data:
        :return: True if suspended or False if not
        """
        return self._plesk_post(guid, data, '?suspend')

    def reinstate(self, guid, data):
        """
        :param guid: plesk guid
        :param data:
        :return: True if reinstated or False if not
        """
        return self._plesk_post(guid, data, '?reinstate')

    def cancel(self): pass

    def block_content(self): pass

    def unblock_content(self): pass

    def delete_content(self): pass

    def _plesk_post(self, guid, data, flag):
        """
        :param guid: plesk guid
        :param data:
        :param flag: ?suspend or ?reinstate
        :return: True if post succeeded or False if post failed
        """
        plesk_shopper = get_host_shopper_id_from_dict(data) + '/'

        try:
            with requests.Session() as session:
                r = session.post(self.url + plesk_shopper + guid + flag, auth=self.auth, headers=self.headers,
                                 data=self.body, verify=False)
            if r.status_code == 200:
                return True
            elif flag == '?suspend':
                logging.error('Failed to suspend GUID: {}, request status code: {}').format(guid, r.status_code)
            elif flag == '?reinstate':
                logging.error('Failed to reinstate GUID: {}, request status code: {}').format(guid, r.status_code)

        except Exception as e:
            logging.error(e.message)
        return False
