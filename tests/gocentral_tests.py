# TODO CMAPT-5272: delete this entire file
from unittest import TestCase

from mock import MagicMock, patch
from requests.exceptions import Timeout

from settings import UnitTestConfig
from zeus.events.suspension.gocentral import GoCentral


class BadTestingConfig():
    GOCENTRAL_SSL_CERT = ''
    GOCENTRAL_SSL_KEY = ''


class TestGoCentral(TestCase):
    GUID = 'test-guid'
    DATA = {'data': {'domainQuery': {'host': {'shopperId': 'test-shopper'}}}}

    def setUp(self):
        self._gocentral = GoCentral(UnitTestConfig)

    # When the request to suspend times out: fail
    @patch('requests.post', side_effect=Timeout())
    def test_suspend_fails(self, mock_post):
        self.assertFalse(self._gocentral.suspend(guid=self.GUID, data=self.DATA))
        mock_post.assert_called()

    # When no guid: fail
    def test_suspend_missing_guid(self):
        self.assertFalse(self._gocentral.suspend(guid=None, data=self.DATA))

    # When no hosting shopper: fail
    def test_suspend_missing_host_shopper(self):
        self.assertFalse(self._gocentral.suspend(guid=self.GUID, data={}))

    # Successful suspension
    @patch('requests.post', return_value=MagicMock(status_code=200))
    def test_suspend_success(self, mock_post):
        self.assertTrue(self._gocentral.suspend(guid=self.GUID, data=self.DATA))
        mock_post.assert_called()

    # Since we dont have a working reinstate method, it will always return false
    @patch('requests.post', return_value=MagicMock(status_code=200))
    def test_reinstate_success(self, mock_post):
        self.assertFalse(self._gocentral.reinstate(guid=self.GUID, data=self.DATA))
        mock_post.assert_not_called()

    # Make sure we get back the expected cert/key pair
    def test_set_certs_success(self):
        _expected_certs = ('cert', 'key')
        _certs = GoCentral._set_certs(UnitTestConfig)
        self.assertEqual(_expected_certs, _certs)

    # Make sure we get back the expected cert/key pair
    def test_set_certs_exception(self):
        self.assertRaises(Exception, GoCentral._set_certs, BadTestingConfig)

    # Make sure nobody changes the XML structure
    def test_get_xml_body_suspend(self):
        expected_xml = """<?xml version="1.0" encoding="utf-8"?>
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
        self.assertEqual(expected_xml, GoCentral._get_xml_body_suspend())
