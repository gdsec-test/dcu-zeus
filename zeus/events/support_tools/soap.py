import time
import requests
import io
import os
import logging
import urllib3

from suds.plugin import MessagePlugin
from suds.client import Client
from suds.transport.http import HttpAuthenticated
from suds.transport import Reply
from suds.sax.text import Raw

from settings import config_by_name


# Plugin for suds to remove empty nodes, this is to fix a bug with the IRIS API
class PrunePlugin(MessagePlugin):
    def marshalled(self, context):
        context.envelope = context.envelope.prune()


# Class to modify suds to use SSL client certs for Auth
class RequestsTransport(HttpAuthenticated):
    def __init__(self, **kwargs):
        self.cert = kwargs.pop('cert', None)
        # super won't work because not using new style class
        HttpAuthenticated.__init__(self, **kwargs)

    def open(self, request):
        self.addcredentials(request)
        with requests.session() as session:
            resp = session.get(request.url,
                               data=request.message,
                               headers=request.headers,
                               cert=self.cert,
                               verify=False,
                               timeout=300)
        result = io.StringIO(resp.content.decode('utf-8'))
        return result

    def send(self, request):
        self.addcredentials(request)
        with requests.session() as session:
            resp = session.post(request.url,
                                data=request.message,
                                headers=request.headers,
                                cert=self.cert,
                                verify=False,
                                timeout=300)
        result = Reply(resp.status_code, resp.headers, resp.content)
        return result


class SoapBase(object):
    _retry_count = 0
    _sleep_time = 10
    _logger = logging.getLogger(__name__)

    def __init__(self):
        env = os.getenv('sysenv') or 'dev'
        if env != 'prod':
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self._config = config_by_name[env]()
        self._retry_max = int(self._config.NETVIO_RETRIES)

    def connect(self):
        self._retry_count = 0

        def get_connection():

            # We will keep looping this function until our retryMax is beyond our limit
            if self._retry_count <= self._retry_max:

                try:
                    # self._url comes from the child
                    self._logger.debug('Attempting to connect to the following WSDL: {}'.format(
                        self._url))
                    headers = {'Content-Type': 'text/xml;charset=UTF-8', 'SOAPAction': ''}

                    auth = {}
                    if hasattr(self, '_client_crt') and hasattr(self, '_client_key'):
                        auth['cert'] = (self._client_crt, self._client_key)
                    if hasattr(self, 'user') and hasattr(self, 'password'):
                        auth['username'] = self.user
                        auth['password'] = self.password
                    t = RequestsTransport(**auth)
                    self.client = Client(
                        self._url,
                        headers=headers,
                        transport=t,
                        plugins=[PrunePlugin()]
                    )

                    if hasattr(self, 'headers'):
                        self.client.set_options(soapheaders=self.headers)
                except Exception as e:
                    self._logger.exception(
                        'Error connecting to {} API. Attempt {}/{} - Error: {}'.format(
                            self._name,
                            self._retry_count,
                            self._retry_max,
                            e.message
                        )
                    )
                    self._retry_count += 1
                    time.sleep(self._sleep_time)
                    return get_connection()
            else:
                self._logger.error('Unable to connect to {} API. after {} attempts'.format(
                    self._name,
                    self._retry_count
                ))
                return None

        return get_connection()

    def req(self, method, input_value):

        self._retry_count = 0

        def run_req():

            # We will keep looping this function until our retryMax is beyond our limit
            if self._retry_count <= self._retry_max:

                try:
                    self._logger.debug('Attempting to use the method {} on the WSDL {}.'.format(
                        method,
                        self._url
                    ))
                    if type(input_value) == Raw:
                        return getattr(self.client.service, method)(input_value)
                    else:
                        return getattr(self.client.service, method)(**input_value)
                except Exception as e:
                    self._logger.exception(
                        'Error on request to {} API. Attempt {}/{} - Error: {}'.format(
                            self._name,
                            self._retry_count,
                            self._retry_max,
                            e.message
                        )
                    )
                    self._retry_count += 1
                    time.sleep(self._sleep_time)
                    return run_req()

            else:
                self._logger.error('Unable to make request to {} API after {} attempts'.format(
                    self._name,
                    self._retry_count
                ))
                return None

        return run_req()
