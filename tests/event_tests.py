import logging
from unittest import TestCase

import mongomock

import mongohandler as handler
from mongohandler import MongoLogFactory
from zeus.events.user_logging.events import generate_event
from zeus.events.user_logging.user_logger import UEVENT


class TestEvents(TestCase):
    def setUp(self):
        self._connection = mongomock.MongoClient()
        self._collection = self._connection.logs.logs
        handler._connection = self._connection
        logging.basicConfig()
        logging.getLogger().addHandler(MongoLogFactory(level=UEVENT, basic_config=True))

    def test_login_event(self):
        generate_event('DCU000123', 'email_sent', more='extra_data')
        data = self._collection.find_one({})
        self.assertEqual(data['message'], 'email_sent')
        self.assertEqual(data['ticket'], 'DCU000123')
        self.assertEqual(data['more'], 'extra_data')
