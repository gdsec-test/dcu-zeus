import json
from unittest import TestCase

from mock import MagicMock, patch

from settings import UnitTestConfig
from zeus.events.suspension.domains import DomainService


class TestDomainService(TestCase):
    domain_name = 'fake.domain'
    entered_by = 'fake_user'
    reason = 'test'
    DOMAIN_ID = '1234'
    KEY_DOMAIN_ID = 'domainId'
    KEY_DOMAIN_IDS = 'domainids'
    KEY_NOTE = 'note'
    KEY_STATUS = 'status'
    KEY_USER = 'user'

    def setUp(self):
        self._domain_service = DomainService(UnitTestConfig.DOMAIN_SERVICE)

    @patch('zeus.events.suspension.domains.requests.post', return_value=None)
    def test_bad_post_request(self, post):
        actual = self._domain_service.suspend_domain(self.domain_name, self.entered_by, self.reason)
        self.assertFalse(actual)

    @patch('zeus.events.suspension.domains.requests.post', return_value=MagicMock(status_code=500, text=json.dumps({})))
    def test_bad_status_code(self, post):
        actual = self._domain_service.suspend_domain(self.domain_name, self.entered_by, self.reason)
        self.assertFalse(actual)

    @patch('zeus.events.suspension.domains.requests.post', return_value=MagicMock(status_code=404, text=json.dumps({})))
    def test_404_status_code(self, post):
        actual = self._domain_service.suspend_domain(self.domain_name, self.entered_by, self.reason)
        self.assertFalse(actual)

    @patch('zeus.events.suspension.domains.requests.post')
    def test_200_no_domain_id(self, post):
        post.return_value = MagicMock(status_code=200, text=json.dumps({self.KEY_DOMAIN_ID: False}))

        actual = self._domain_service.suspend_domain(self.domain_name, self.entered_by, self.reason)
        self.assertFalse(actual)

    @patch('zeus.events.suspension.domains.requests.post')
    def test_200_no_status(self, post):
        post.return_value = MagicMock(status_code=200, text=json.dumps({self.KEY_DOMAIN_ID: self.DOMAIN_ID,
                                                                        self.KEY_STATUS: False}))

        actual = self._domain_service.suspend_domain(self.domain_name, self.entered_by, self.reason)
        self.assertFalse(actual)

    @patch('zeus.events.suspension.domains.requests.post')
    def test_200_invalid_state(self, post):
        post.return_value = MagicMock(status_code=200, text=json.dumps({self.KEY_DOMAIN_ID: self.DOMAIN_ID,
                                                                        self.KEY_STATUS: 'SUSPENDED'}))

        actual = self._domain_service.suspend_domain(self.domain_name, self.entered_by, self.reason)
        self.assertFalse(actual)

    @patch.object(DomainService, '_suspend', return_value=False)
    @patch('zeus.events.suspension.domains.requests.post')
    def test_200_valid_state_failed_suspension(self, post, suspend):
        post.return_value = MagicMock(status_code=200, text=json.dumps({self.KEY_DOMAIN_ID: self.DOMAIN_ID,
                                                                        self.KEY_STATUS: 'AWAITING_VERIFICATION_ICANN'}))

        actual = self._domain_service.suspend_domain(self.domain_name, self.entered_by, self.reason)
        self.assertFalse(actual)

    @patch.object(DomainService, '_suspend', return_value=1)
    @patch('zeus.events.suspension.domains.requests.post')
    def test_200_valid_state(self, post, suspend):
        post.return_value = MagicMock(status_code=200, text=json.dumps({self.KEY_DOMAIN_ID: self.DOMAIN_ID,
                                                                        self.KEY_STATUS: 'ACTIVE'}))

        actual = self._domain_service.suspend_domain(self.domain_name, self.entered_by, self.reason)
        self.assertEqual(actual, 1)

    @patch('zeus.events.suspension.domains.requests.post', return_value=MagicMock(text=json.dumps({'count': '1'})))
    def test_suspend(self, post):
        payload = {self.KEY_DOMAIN_IDS: [self.DOMAIN_ID], self.KEY_USER: self.entered_by, self.KEY_NOTE: self.reason}

        actual = self._domain_service._suspend(payload)
        self.assertEqual(actual, 1)

    @patch('zeus.events.suspension.domains.requests.post', return_value=None)
    def test_suspend_failed(self, post):
        payload = {self.KEY_DOMAIN_IDS: [self.DOMAIN_ID], self.KEY_USER: self.entered_by, self.KEY_NOTE: self.reason}

        actual = self._domain_service._suspend(payload)
        self.assertFalse(actual)
