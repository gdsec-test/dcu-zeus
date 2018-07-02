import json
import logging
import requests


class DomainService:
    VALID_STATES = ['ACTIVE']

    def __init__(self, endpoint):
        self._logger = logging.getLogger(__name__)
        domain_uri = 'http://{}/v1/domains'.format(endpoint)
        self._query_domain_endpoint = '{}/domaininfo'.format(domain_uri)
        self._suspend_domain_endpoint = '{}/suspenddomain'.format(domain_uri)

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
            with requests.Session() as session:
                resp = session.post(self._query_domain_endpoint, data=json.dumps({"domain": domain_name}))
            resp_dict = json.loads(resp.text)
            status_code = int(resp.status_code)

            # So far, I've received the following status_code responses:
            #  200: u'{"shopperId":"1274145"}'
            #  400: u'{"error":"invalid character \'d\' looking for beginning of value","code":3}'
            #  404: u'Not Found\n'
            #  500: u'{"error":"No Active shoppers for this Domain Name","code":13}'
            if status_code not in [200, 404]:
                self._logger.error('Domain lookup failed for {} with status code {} : {}'.format(domain_name,
                                                                                                 status_code,
                                                                                                 resp.text))
            elif status_code == 404:
                self._logger.critical('URL not found : {}'.format(resp.text))
            elif status_code == 200:
                # Valid response looks like:
                #  {"domain":"XXX",
                #   "shopperId":"XXX",
                #   "domainId":###,
                #   "createDate":"XXX",
                #   "status":"XXX"}
                if not resp_dict.get('domainId', False):
                    self._logger.error('No domain id returned from domainservice query on {}'.format(domain_name))
                elif not resp_dict.get('status', False):
                    self._logger.error('No status returned from domainservice query on {}'.format(domain_name))
                else:
                    status = resp_dict.get('status')
                    if status in self.VALID_STATES:
                        self._logger.info("resp {}".format(resp.text))
                        payload = {"domainids": [str(resp_dict.get('domainId'))],
                                   "user": entered_by,
                                   "note": reason}

                        return_value = self._suspend(payload)
                        if not return_value:
                            self._logger.error('Domain suspension failed for {}: {}'.format(domain_name, status))

                    else:
                        self._logger.error("Unable to suspend domain {}. Currently in state {}".format(domain_name,
                                                                                                       status))
        except Exception as e:
            self._logger.error('Exception: {}'.format(e))
        return return_value

    def _suspend(self, payload):
        return_value = False
        # Attempt to suspend the domain
        try:
            with requests.Session() as session:
                resp = session.post(self._suspend_domain_endpoint, data=json.dumps(payload))

            # Check for expected return value
            # Expected domain suspension response looks like:
            #  {"count":1}
            resp_text = json.loads(resp.text)
            if resp_text.get('count', False):
                self._logger.info("{} domains affected".format(resp_text.get('count')))
                return_value = int(resp_text.get('count')) > 0
        except Exception as e:
            self._logger.error(e.message)
        finally:
            return return_value
