import logging
import os

import pymongo
from log4mongo.handlers import MongoFormatter, MongoHandler
from pymongo.collection import Collection
from pymongo.errors import OperationFailure

from settings import config_by_name

try:
    from pymongo import MongoClient as Connection
except ImportError:
    from pymongo import Connection


if pymongo.version_tuple[0] >= 3:
    write_method = 'insert_one'
else:
    write_method = 'save'

_connection = None


class MongoLogFactory(MongoHandler):
    """
    Custom implementation of MongoHandler to avoid connection issues
    """

    def __init__(self, level=logging.NOTSET, logging_config=None, basic_config=None):
        if basic_config:
            super(MongoLogFactory, self).__init__(level=level)
        else:
            config = logging_config if logging_config else config_by_name[os.getenv('sysenv', 'dev')]()
            super(MongoLogFactory, self).__init__(level=level, host=config.DB_HOST, username=config.DB_USER,
                                                  password=config.DB_PASS, authentication_db=config.DB,
                                                  database_name=config.DB, collection=config.LOGGING_COLLECTION,
                                                  formatter=MongoFormatter())

    def _connect(self, **kwargs):
        """
        Overriding original implimentation that tried to use is_locked which requires admin privileges
        :param kwargs:
        :return:
        """
        """Connecting to mongo database."""
        global _connection
        if self.reuse and _connection:
            self.connection = _connection
        else:
            if os.getenv("sysenv") in ["dev", "test"]:
                self.connection = Connection(host=self.host, port=self.port, connect=False, tls=True, tlsCertificateKeyFile=os.getenv("MONGO_CLIENT_CERT"), **kwargs)
            else:
                self.connection = Connection(host=self.host, port=self.port, connect=False, **kwargs)
        _connection = self.connection

        self.db = self.connection[self.database_name]
        if self.username is not None and self.password is not None:
            auth_db = self.connection[self.authentication_database_name]
            self.authenticated = auth_db.authenticate(self.username,
                                                      self.password)

        if self.capped:
            #
            # We don't want to override the capped collection
            # (and it throws an error anyway)
            try:
                self.collection = Collection(self.db, self.collection_name,
                                             capped=True, max=self.capped_max,
                                             size=self.capped_size)
            except OperationFailure:
                # Capped collection exists, so get it.
                self.collection = self.db[self.collection_name]
        else:
            self.collection = self.db[self.collection_name]
