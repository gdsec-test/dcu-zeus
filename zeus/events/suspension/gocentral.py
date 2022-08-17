import logging

import requests
from csetutils.appsec.logging import get_logging
from requests.packages.urllib3.exceptions import (InsecurePlatformWarning,
                                                  InsecureRequestWarning)

from zeus.events.suspension.interface import Product
from zeus.utils.functions import get_host_info_from_dict

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)


class GoCentral(Product):
    KEY_DATA = 'data'
    KEY_TICKET_ID_K = 'ticketID'
    KEY_TICKET_ID_P = 'ticketId'
    KEY_SHOPPER_ID_K = 'shopperID'
    KEY_SHOPPER_ID_P = 'shopperId'
    """
    Using the SOAP API endpoint, send an abuse suspension event for a GoCentral guid
    """
    _headers = {'Content-Type': 'text/xml',
                'SOAPAction': 'http://schemas.orion.starfieldtech.com/account/Suspend'}

    def __init__(self, app_settings):
        self._logger = logging.getLogger('celery.tasks')
        self._url = app_settings.GOCENTRAL_URL
        self._cert = GoCentral._set_certs(app_settings)

    @staticmethod
    def _set_certs(config):
        """
        If no cert or key, throw an exception to kill the service
        """
        if not config.GOCENTRAL_SSL_CERT or not config.GOCENTRAL_SSL_KEY:
            raise Exception('Cert/key not provided for GoCentral')

        return config.GOCENTRAL_SSL_CERT, config.GOCENTRAL_SSL_KEY

    def suspend(self, guid, **kwargs):
        """
        Call SOAP endpoint with xml body to set Orion suspension event for the GoCentral guid
        :param guid: string of hosting guid
        :param kwargs: dict containing ticket key/value pairs
        """
        try:
            ticket = kwargs.get(self.KEY_DATA, {})
            ticket_id = ticket.get(self.KEY_TICKET_ID_P, ticket.get(self.KEY_TICKET_ID_K))
            host_dict = get_host_info_from_dict(ticket)
            host_shopper = host_dict.get(self.KEY_SHOPPER_ID_P, host_dict.get(self.KEY_SHOPPER_ID_K))
            self._logger.debug(f'Calling {self._url} to suspend {guid}:{host_shopper} with cert: {self._cert}')
            if not guid or not host_shopper:
                raise Exception(f'Missing guid or hosting shopper for {ticket_id}')

            xml_body = GoCentral._get_xml_body_suspend().format(guid=guid, shopperid=host_shopper)
            r = requests.post(self._url,
                              data=xml_body,
                              headers=self._headers,
                              cert=self._cert,
                              verify=False)
            if r.status_code not in [200]:
                self._logger.error(f'Bad status code {r.status_code} in suspend response')
                return False
            self._logger.info(f'Suspended GoCentral ticket {ticket_id}')
            appseclogger = get_logging("dev", "zeus")
            appseclogger.info("suspending gocentral product", extra={"event": {"kind": "event",
                                                                               "category": "process",
                                                                               "type": ["change", "user"],
                                                                               "outcome": "success",
                                                                               "action": "suspend"},
                                                                     "suspension": {"guid": guid,
                                                                                    "host_shopper": host_shopper}})
            return True
        except Exception as e:
            self._logger.error(f'Unable to suspend GoCentral product: {e}')
            return False

    def reinstate(self, guid, **kwargs):
        host_dict = get_host_info_from_dict(kwargs.get(self.KEY_DATA, {}))
        host_shopper = host_dict.get(self.KEY_SHOPPER_ID_P, host_dict.get(self.KEY_SHOPPER_ID_K))
        self._logger.debug(f'Calling endpoint to reinstate {guid}:{host_shopper} with cert: {self._cert}')
        return False

    def cancel(self):
        pass

    def block_content(self):
        pass

    def unblock_content(self):
        pass

    def delete_content(self):
        pass

    @staticmethod
    def _get_xml_body_suspend():
        return """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <Suspend xmlns="http://schemas.orion.starfieldtech.com/account">
      <MessageID></MessageID>
      <Requests>
        <OperationRequest>
          <RequestIdx>123</RequestIdx>
          <Identifier>
            <SystemNamespace>GoDaddy</SystemNamespace>
            <ResellerId>1</ResellerId>
            <CustomerNum>{shopperid}</CustomerNum>
            <AccountUid>{guid}</AccountUid>
          </Identifier>
          <dtl>
            <RequestedBy>dcu</RequestedBy>
            <RequestedByLoginName>dcu</RequestedByLoginName>
            <ReasonForRequest>suspend for abuse</ReasonForRequest>
            <Messages xsi:nil="true" />
          </dtl>
          <objType>ACCOUNT</objType>
          <opType>ABUSE_SUSPEND</opType>
          <ObjectUid>{guid}</ObjectUid>
          <requestItems>
            <RequestItem>
                <ItemName>TYPE</ItemName>
                <ItemValue>ABUSE</ItemValue>
            </RequestItem>
          </requestItems>
        </OperationRequest>
      </Requests>
    </Suspend>
  </soap:Body>
</soap:Envelope>"""
