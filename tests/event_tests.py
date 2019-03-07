import logging

import mongomock
from nose.tools import assert_equal

import mongohandler as handler
from mongohandler import MongoLogFactory
from zeus.events.user_logging.events import generate_event
from zeus.events.user_logging.user_logger import UEVENT


class TestEvents:
    @classmethod
    def setup(cls):
        cls._connection = mongomock.MongoClient()
        cls._collection = cls._connection.logs.logs
        handler._connection = cls._connection
        logging.basicConfig()
        logging.getLogger().addHandler(MongoLogFactory(level=UEVENT, basic_config=True))

    def test_login_event(self):
        generate_event('DCU000123', 'email_sent', more='extra_data')
        data = self._collection.find_one({})
        assert_equal(data['message'], 'email_sent')
        assert_equal(data['ticket'], 'DCU000123')
        assert_equal(data['more'], 'extra_data')
