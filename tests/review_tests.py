from datetime import datetime, timedelta

import mongomock
from dcdatabase.phishstorymongo import PhishstoryMongo
from nose.tools import assert_true

from settings import TestingConfig
from zeus.reviews.reviews import BasicReview, FraudReview, SucuriReview


class TestReview:
    sucuri_hold_reason = '72hr_notice_sent'

    @classmethod
    def setup(cls):
        cls._config = TestingConfig()
        cls._db = PhishstoryMongo(cls._config)
        # replace collection with mock
        cls._db._mongo._collection = mongomock.MongoClient().db.collection
        cls._db.add_new_incident(1236, dict(sourceDomainOrIp='lmn.com'))
        cls._db.add_new_incident(1237, dict(sourceDomainOrIp='abc.com'))
        cls._db.add_new_incident(1238, dict(sourceDomainOrIp='xyz.com'))

        cls._basic = BasicReview(cls._config)
        cls._basic._db = cls._db  # Replace db with mock

        cls._fraud = FraudReview(cls._config)
        cls._fraud._db = cls._db  # Replace db with mock

        cls._sucuri = SucuriReview(cls._config)
        cls._sucuri._db = cls._db  # Replace db with mock

    def test_basic_hold(self):
        doc = self._basic.place_in_review(1236, datetime.utcnow() + timedelta(seconds=self._config.HOLD_TIME))
        assert_true(doc['hold_until'])

    def test_basic_hold_with_reason(self):
        doc = self._basic.place_in_review(1236, datetime.utcnow() + timedelta(seconds=self._config.HOLD_TIME),
                                          'New Account')
        assert_true(doc['hold_until'])
        assert_true(doc['hold_reason'])

    def test_fraud_hold_with_reason(self):
        doc = self._fraud.place_in_review(1237, datetime.utcnow() + timedelta(seconds=self._config.HOLD_TIME),
                                          'New Account')
        assert_true(doc['fraud_hold_until'])
        assert_true(doc['fraud_hold_reason'])

    def test_fraud_hold(self):
        doc = self._fraud.place_in_review(1237, datetime.utcnow() + timedelta(seconds=self._config.HOLD_TIME))
        assert_true(doc['fraud_hold_until'])

    def test_sucuri_hold(self):
        doc = self._sucuri.place_in_review(1238, datetime.utcnow() + timedelta(seconds=self._config.SUCURI_HOLD_TIME))
        assert_true(doc['sucuri_hold_until'])

    def test_sucuri_hold_with_reason(self):
        doc = self._sucuri.place_in_review(1238, datetime.utcnow() + timedelta(seconds=self._config.SUCURI_HOLD_TIME),
                                           self.sucuri_hold_reason)
        assert_true(doc['sucuri_hold_until'])
        assert_true(doc['sucuri_hold_reason'])
        assert_true(doc.get('sucuri_hold_reason', self.sucuri_hold_reason))
