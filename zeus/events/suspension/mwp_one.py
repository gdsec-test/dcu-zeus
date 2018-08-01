import logging

import requests
from requests.packages.urllib3.exceptions import InsecurePlatformWarning, InsecureRequestWarning

from zeus.events.suspension.interface import Product

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)


class MWPOne(Product):
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def __init__(self, app_settings):
        self.mwpone_url = app_settings.MWPONE_URL
        self.mwponeauth = (app_settings.MWPONEUSER, app_settings.MWPONEPASS)

    def suspend(self, accountid):
        url = self.mwpone_url + accountid + '?suspendAccount'

        try:
            response = requests.post(url, auth=self.mwponeauth, headers=self.headers, verify=False)

            if response.text == 'true':
                logging.info('Managed Wordpress 1.0 account {} has been suspended'.format(accountid))
                return True

        except Exception as e:
            logging.error("Failed to suspend account {}. {}".format(accountid, e.message))
        return False

    def reinstate(self, accountid):
        url = self.mwpone_url + accountid + '?unsuspendAccount'

        try:
            response = requests.post(url, auth=self.mwponeauth, headers=self.headers, verify=False)
            if response.text == 'true':
                logging.info('Managed Wordpress 1.0 account {} has been reinstated'.format(accountid))
                return True

        except Exception as e:
            logging.error("Failed to reinstate account {}. {}".format(accountid, e.message))
        return False

    def cancel(self):
        pass

    def block_content(self):
        pass

    def unblock_content(self):
        pass

    def delete_content(self):
        pass
