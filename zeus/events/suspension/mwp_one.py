import logging

import requests
from requests.packages.urllib3.exceptions import (InsecurePlatformWarning,
                                                  InsecureRequestWarning)

from zeus.events.suspension.interface import Product

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)


class MWPOne(Product):
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def __init__(self, app_settings):
        self.mwpone_url = app_settings.MWPONE_URL
        self.mwponeauth = (app_settings.MWPONEUSER, app_settings.MWPONEPASS)

    def suspend(self, guid, **kwargs):
        url = self.mwpone_url + guid + '?suspendAccount'

        try:
            response = requests.post(url, auth=self.mwponeauth, headers=self.headers, verify=False)
            if response.status_code == 200:
                if response.text == 'true':
                    logging.info('Managed Wordpress 1.0 account {} has been suspended'.format(guid))
                    return True
            else:
                print 'Failed to suspend account {}: {}'.format(guid, response.reason)

        except Exception as e:
            logging.error("Failed to suspend account {}. {}".format(guid, e.message))
        return False

    def reinstate(self, guid, **kwargs):
        url = self.mwpone_url + guid + '?unsuspendAccount'

        try:
            response = requests.post(url, auth=self.mwponeauth, headers=self.headers, verify=False)
            if response.status_code == 200:
                if response.text == 'true':
                    logging.info('Managed Wordpress 1.0 account {} has been reinstated'.format(guid))
                    return True
            else:
                print 'Failed to reinstate account {}: {}'.format(guid, response.reason)

        except Exception as e:
            logging.error("Failed to reinstate account {}. {}".format(guid, e.message))
        return False

    def cancel(self):
        pass

    def block_content(self):
        pass

    def unblock_content(self):
        pass

    def delete_content(self):
        pass
