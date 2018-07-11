import json
import logging

import requests
from requests.packages.urllib3.exceptions import InsecurePlatformWarning, InsecureRequestWarning

# TODO Uncomment import and add 'Product' back as param in Angelo Class
# from zeus.events.suspension.interface import Product

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)


class Angelo():

    # TODO Add 'app_settings' back as second param in init
    def __init__(self):

        # TODO Remove duplicate URL and auth to use settings

        # self.auth = (app_settings.PLESKUSER, app_settings.PLESKPASS)
        self.auth = ('REDACTED', 'REDACTED')

        # TODO Diablo has an enable FTP option. Find out if plesk has this, and do we want to allow it here too?
        self.body = json.dumps({"disable_panel": "true", "reason": "DCU Testing", "type": "abuse"}, ensure_ascii=False)

        self.headers = {"Accept": "application/json", "Content-Type": "application/json"}

        # self.url = app_settings.PLESK_URL
        self.url = 'https://p3nwplskapp-v01.shr.prod.phx3.secureserver.net:8084/v1/accounts/'

    def suspend(self, shopper_id, guid):
        plesk_shopper = shopper_id + '/'
        flag = '?suspend'

        try:
            with requests.Session() as session:
                r = session.post(self.url + plesk_shopper + guid + flag, auth=self.auth, headers=self.headers,
                                 data=self.body, verify=False)
            if r.status_code == 200:
                return True
            else:
                logging.error('Failed to suspend GUID: {}, request status code: {}').format(guid, r.status_code)

        except Exception as e:
            logging.error(e.message)
        return False

    def reinstate(self, shopper_id, guid):
        plesk_shopper = shopper_id + '/'
        flag = '?reinstate'

        try:
            with requests.Session() as session:
                r = session.post(self.url + plesk_shopper + guid + flag, auth=self.auth, headers=self.headers,
                                 data=self.body, verify=False)
            if r.status_code == 200:
                return True
            else:
                logging.error('Failed to reinstate GUID: {}, request status code: {}').format(guid, r.status_code)

        except Exception as e:
            logging.error(e.message)
        return False

    def cancel(self): pass

    def block_content(self): pass

    def unblock_content(self): pass

    def delete_content(self): pass
