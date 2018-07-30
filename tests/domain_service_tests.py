import json

from mock import patch, MagicMock
from nose.tools import assert_equal, assert_false

from settings import TestingConfig
from zeus.events.suspension.domains import DomainService


class TestDomainService:
    domain_name = 'fake.domain'
    entered_by = 'fake_user'
    reason = 'test'

    @classmethod
    def setup(cls):
        cls._domain_service = DomainService(TestingConfig.DOMAIN_SERVICE)

    @patch('zeus.events.suspension.domains.requests.post', return_value=None)
    def test_bad_post_request(self, post):
        actual = self._domain_service.suspend_domain(self.domain_name, self.entered_by, self.reason)
        assert_false(actual)

    @patch('zeus.events.suspension.domains.requests.post', return_value=MagicMock(status_code=500, text=json.dumps({})))
    def test_bad_status_code(self, post):
        actual = self._domain_service.suspend_domain(self.domain_name, self.entered_by, self.reason)
        assert_false(actual)

    @patch('zeus.events.suspension.domains.requests.post', return_value=MagicMock(status_code=404, text=json.dumps({})))
    def test_404_status_code(self, post):
        actual = self._domain_service.suspend_domain(self.domain_name, self.entered_by, self.reason)
        assert_false(actual)

    @patch('zeus.events.suspension.domains.requests.post')
    def test_200_no_domain_id(self, post):
        post.return_value = MagicMock(status_code=200, text=json.dumps({'domainId': False}))

        actual = self._domain_service.suspend_domain(self.domain_name, self.entered_by, self.reason)
        assert_false(actual)

    @patch('zeus.events.suspension.domains.requests.post')
    def test_200_no_status(self, post):
        post.return_value = MagicMock(status_code=200, text=json.dumps({'domainId': '1234', 'status': False}))

        actual = self._domain_service.suspend_domain(self.domain_name, self.entered_by, self.reason)
        assert_false(actual)

    @patch('zeus.events.suspension.domains.requests.post')
    def test_200_invalid_state(self, post):
        post.return_value = MagicMock(status_code=200, text=json.dumps({'domainId': '1234', 'status': 'SUSPENDED'}))

        actual = self._domain_service.suspend_domain(self.domain_name, self.entered_by, self.reason)
        assert_false(actual)

    @patch.object(DomainService, '_suspend', return_value=False)
    @patch('zeus.events.suspension.domains.requests.post')
    def test_200_valid_state_failed_suspension(self, post, suspend):
        post.return_value = MagicMock(status_code=200, text=json.dumps({'domainId': '1234', 'status': 'ACTIVE'}))

        actual = self._domain_service.suspend_domain(self.domain_name, self.entered_by, self.reason)
        assert_false(actual)

    @patch.object(DomainService, '_suspend', return_value=1)
    @patch('zeus.events.suspension.domains.requests.post')
    def test_200_valid_state(self, post, suspend):
        post.return_value = MagicMock(status_code=200, text=json.dumps({'domainId': '1234', 'status': 'ACTIVE'}))

        actual = self._domain_service.suspend_domain(self.domain_name, self.entered_by, self.reason)
        assert_equal(actual, 1)

    @patch('zeus.events.suspension.domains.requests.post', return_value=MagicMock(text=json.dumps({'count': '1'})))
    def test_suspend(self, post):
        payload = {'domainids': ['1234'], 'user': self.entered_by, 'note': self.reason}

        actual = self._domain_service._suspend(payload)
        assert_equal(actual, 1)

    @patch('zeus.events.suspension.domains.requests.post', return_value=None)
    def test_suspend_failed(self, post):
        payload = {'domainids': ['1234'], 'user': self.entered_by, 'note': self.reason}

        actual = self._domain_service._suspend(payload)
        assert_false(actual)
