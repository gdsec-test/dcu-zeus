import json
import logging

import requests

from zeus.persist.notification_timeouts import Throttle


class ThrottledDomainService:

    def __init__(self, app_settings):
        self._decorated = DomainService(app_settings.DOMAIN_SERVICE)
        self._throttle = Throttle(app_settings.REDIS, app_settings.SUSPEND_DOMAIN_LOCK_TIME)

    def can_suspend_domain(self, domain):
        return self._throttle.can_suspend_domain(domain)

    def suspend_domain(self, domain, entered_by, reason):
        return self._decorated.suspend_domain(domain, entered_by, reason)


class DomainService:
    VALID_STATES = {'ACTIVE',
                    'AWAITING_VERIFICATION_ICANN',
                    'AWAITING_VERIFICATION_ICANN_MANUAL'
                    }

    def __init__(self, endpoint):
        self._logger = logging.getLogger('celery.tasks')
        domain_uri = f'http://{endpoint}/v1/domains'
        self._query_domain_endpoint = f'{domain_uri}/domaininfo'
        self._suspend_domain_endpoint = f'{domain_uri}/suspenddomain'

    def suspend_domain(self, domain_name, entered_by, reason):
        """
        Suspends a domain name if the domain is owned by GoDaddy i.e. a
        shopper is associated with the domain and the domain is in one of
        the VALID_STATES.
        NOTE: Both the connection and call to the gRPC service are bound by
        a 5 second timeout
        :param domain_name:
        :param entered_by: name of entity/person suspending domain
        :param reason: reason this domain is being suspended
        :return: bool
        """
        return_value = False
        try:
            # Query the domain to get status
            resp = requests.post(self._query_domain_endpoint, data=json.dumps({'domain': domain_name}))
            resp_dict = json.loads(resp.text)

            # So far, I've received the following status_code responses:
            #  200: u'{"shopperId":"1274145"}'
            #  400: u'{"error":"invalid character \'d\' looking for beginning of value","code":3}'
            #  404: u'Not Found\n'
            #  500: u'{"error":"No Active shoppers for this Domain Name","code":13}'
            if resp.status_code not in [200, 404]:
                self._logger.error(
                    f'Domain lookup failed for {domain_name} with status code {resp.status_code} : {resp.text}')
            elif resp.status_code == 404:
                self._logger.error(f'URL not found : {resp.text}')

            elif resp.status_code == 200:
                #  Example resp: {"domain":"XXX", "shopperId":"XXX", "domainId":###, "createDate":"XXX", "status":"XXX"}
                if not resp_dict.get('domainId'):
                    self._logger.error(f'No domain id returned from domainservice query on {domain_name}')
                elif not resp_dict.get('status'):
                    self._logger.error(f'No status returned from domainservice query on {domain_name}')
                else:
                    status = resp_dict.get('status')
                    if status in self.VALID_STATES:
                        payload = {'domainids': [str(resp_dict.get('domainId'))], 'user': entered_by, 'note': reason}

                        return_value = self._suspend(payload)
                        if not return_value:
                            self._logger.error(f'Domain suspension failed for {domain_name}: {status}')
                    else:
                        self._logger.error(f'Unable to suspend domain {domain_name}. Currently in state {status}')
        except Exception as e:
            self._logger.error(e)
        return return_value

    def _suspend(self, payload):
        return_value = False
        try:
            resp = requests.post(self._suspend_domain_endpoint, data=json.dumps(payload))

            # Expected domain suspension response looks like: {"count":1}
            resp_text = json.loads(resp.text)
            if resp_text.get('count'):
                self._logger.info("{} domains affected".format(resp_text.get('count')))
                return_value = int(resp_text.get('count')) > 0
        except Exception as e:
            self._logger.error(e)
        return return_value
