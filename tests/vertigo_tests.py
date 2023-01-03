# TODO CMAPT-5272: delete this entire file
from unittest import TestCase

from mock import MagicMock, patch
from requests.exceptions import Timeout

from settings import UnitTestConfig
from zeus.events.suspension.vertigo import Vertigo


class TestVertigo(TestCase):
    def setUp(self):
        self.vertigo = Vertigo(UnitTestConfig)

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
        self.assertFalse(self.vertigo.suspend('test-guid', data))

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
        self.assertTrue(self.vertigo.suspend('test-guid', data))
