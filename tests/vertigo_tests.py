# TODO CMAPT-5272: delete this entire file
from mock import MagicMock, patch
from nose.tools import assert_false, assert_true
from requests.exceptions import Timeout

from settings import UnitTestConfig
from zeus.events.suspension.vertigo import Vertigo


class TestVertigo:
    @classmethod
    def setup(cls):
        cls.vertigo = Vertigo(UnitTestConfig)

    @patch('requests.post', side_effect=Timeout())
    def test_suspend_fails(self, post):
        data = {"data": {
            "domainQuery": {
                "host": {
                    "product": "Vertigo",
                    "guid": "28fa828c-5500-11e4-b427-14feb5d40b65",
                    "containerID": "0000"
                }
            }
        }
        }
        assert_false(self.vertigo.suspend('test-guid', data))

    @patch('requests.post', return_value=MagicMock(status_code=202))
    def test_suspend_success(self, post):
        data = {"data": {
            "domainQuery": {
                "host": {
                    "product": "Vertigo",
                    "guid": "28fa828c-5500-11e4-b427-14feb5d40b65",
                    "containerID": "0000"
                }
            }
        }
        }
        assert_true(self.vertigo.suspend('test-guid', data))
