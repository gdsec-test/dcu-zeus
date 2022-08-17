import logging

import requests
from csetutils.appsec.logging import get_logging
from requests.packages.urllib3.exceptions import (InsecurePlatformWarning,
                                                  InsecureRequestWarning)

from settings import AppConfig
from zeus.events.suspension.interface import Product

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)


class MWPOne(Product):
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

    def __init__(self, app_settings: AppConfig):
        self._logger = logging.getLogger('celery.tasks')
        self.mwpone_url = app_settings.MWPONE_URL
        self.cert = (app_settings.CMAP_API_CERT, app_settings.CMAP_API_KEY)

    def suspend(self, guid, **kwargs):
        url = self.mwpone_url + guid + '?suspendAccount'

        try:
            response = requests.post(url, cert=self.cert, headers=self.headers, verify=False)
            if response.status_code == 200:
                if response.text == 'true':
                    self._logger.info(f'Managed Wordpress 1.0 account {guid} has been suspended')
                    appseclogger = get_logging("dev", "zeus")
                    appseclogger.info("suspending mwp product", extra={"event": {"kind": "event",
                                                                                 "category": "process",
                                                                                 "type": ["change", "user"],
                                                                                 "outcome": "success",
                                                                                 "action": "suspend"},
                                                                       "guid": guid})
                    return True
            else:
                self._logger.error(f'Failed to suspend account {guid}: {response.reason}')

        except Exception as e:
            self._logger.error(f'Failed to suspend account {guid}. {e}')
        return False

    def reinstate(self, guid, **kwargs):
        url = self.mwpone_url + guid + '?unsuspendAccount'

        try:
            response = requests.post(url, cert=self.cert, headers=self.headers, verify=False)
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
