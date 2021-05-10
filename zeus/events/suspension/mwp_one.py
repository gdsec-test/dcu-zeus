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
        self._logger = logging.getLogger(__name__)
        self.mwpone_url = app_settings.MWPONE_URL
        self.mwponeauth = (app_settings.MWPONEUSER, app_settings.MWPONEPASS)

    def suspend(self, guid, **kwargs):
        url = self.mwpone_url + guid + '?suspendAccount'

        try:
            response = requests.post(url, auth=self.mwponeauth, headers=self.headers, verify=False)
            if response.status_code == 200:
                if response.text == 'true':
                    self._logger.info(f'Managed Wordpress 1.0 account {guid} has been suspended')
                    return True
            else:
                self._logger.error(f'Failed to suspend account {guid}: {response.reason}')

        except Exception as e:
            self._logger.error(f'Failed to suspend account {guid}. {e}')
        return False

    def reinstate(self, guid, **kwargs):
        url = self.mwpone_url + guid + '?unsuspendAccount'

        try:
            response = requests.post(url, auth=self.mwponeauth, headers=self.headers, verify=False)
            if response.status_code == 200:
                if response.text == 'true':
                    self._logger.info(f'Managed Wordpress 1.0 account {guid} has been reinstated')
                    return True
            else:
                self._logger.error(f'Failed to reinstate account {guid}: {response.reason}')

        except Exception as e:
            self._logger.error(f'Failed to reinstate account {guid}. {e}')
        return False

    def cancel(self):
        pass

    def block_content(self):
        pass

    def unblock_content(self):
        pass

    def delete_content(self):
        pass
