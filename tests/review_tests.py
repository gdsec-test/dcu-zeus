import mongomock
from dcdatabase.phishstorymongo import PhishstoryMongo
from nose.tools import assert_equal, assert_is_none, assert_is_not_none

from settings import TestingConfig
from zeus.reviews.reviews import BasicReview, FraudReview, SucuriReview


class TestReview:
    HOLD_REASON = 'New Account'
    HOLD_TIME = 'Hold Time'
    KEY_FRAUD_HOLD_REASON = 'fraud_hold_reason'
    KEY_FRAUD_HOLD_UNTIL = 'fraud_hold_until'
    KEY_HOLD_REASON = 'hold_reason'
    KEY_HOLD_UNTIL = 'hold_until'
    SUCURI_HOLD_REASON = '72hr_notice_sent'

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
        doc = self._basic.place_in_review(1236, self.HOLD_TIME)
        assert_is_not_none(doc.get(self.KEY_HOLD_UNTIL))
        assert_is_none(doc.get(self.KEY_HOLD_REASON))
        assert_equal(doc.get(self.KEY_HOLD_UNTIL), self.HOLD_TIME)

    def test_basic_hold_with_reason(self):
        doc = self._basic.place_in_review(1236, self.HOLD_TIME, self.HOLD_REASON)
        assert_is_not_none(doc.get(self.KEY_HOLD_UNTIL))
        assert_is_not_none(doc.get(self.KEY_HOLD_REASON))
        assert_equal(doc.get(self.KEY_HOLD_UNTIL), self.HOLD_TIME)
        assert_equal(doc.get(self.KEY_HOLD_REASON), self.HOLD_REASON)

    def test_fraud_hold_with_reason(self):
        doc = self._fraud.place_in_review(1237, self.HOLD_TIME, self.HOLD_REASON)
        assert_is_not_none(doc.get(self.KEY_FRAUD_HOLD_UNTIL))
        assert_is_not_none(doc.get(self.KEY_FRAUD_HOLD_REASON))
        assert_equal(doc.get(self.KEY_FRAUD_HOLD_UNTIL), self.HOLD_TIME)
        assert_equal(doc.get(self.KEY_FRAUD_HOLD_REASON), self.HOLD_REASON)

    def test_fraud_hold(self):
        doc = self._fraud.place_in_review(1237, self.HOLD_TIME)
        assert_is_not_none(doc.get(self.KEY_FRAUD_HOLD_UNTIL))
        assert_is_none(doc.get(self.KEY_FRAUD_HOLD_REASON))
        assert_equal(doc.get(self.KEY_FRAUD_HOLD_UNTIL), self.HOLD_TIME)

    def test_sucuri_hold(self):
        doc = self._sucuri.place_in_review(1238, self.HOLD_TIME)
        assert_is_not_none(doc.get(self.KEY_HOLD_UNTIL))
        assert_is_none(doc.get(self.KEY_HOLD_REASON))
        assert_equal(doc.get(self.KEY_HOLD_UNTIL), self.HOLD_TIME)

    def test_sucuri_hold_with_reason(self):
        """
        Sucuri holds use the same 'hold_until' and 'hold_reason' fields
        """
        doc = self._sucuri.place_in_review(1238, self.HOLD_TIME, self.SUCURI_HOLD_REASON)
        assert_is_not_none(doc.get(self.KEY_HOLD_UNTIL))
        assert_is_not_none(doc.get(self.KEY_HOLD_REASON))
        assert_equal(doc.get(self.KEY_HOLD_UNTIL), self.HOLD_TIME)
        assert_equal(doc.get(self.KEY_HOLD_REASON), self.SUCURI_HOLD_REASON)
